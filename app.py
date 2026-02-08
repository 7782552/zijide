from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import g4f
import json

app = Flask(__name__)
CORS(app)

# 打印可用的 providers（调试用）
print("Available providers:", dir(g4f.Provider))

# ✅ 只使用确定存在的 Provider
STABLE_MODELS = {
    "gpt-4o-mini": {
        "provider": g4f.Provider.DDG,
        "model": "gpt-4o-mini",
    },
    "gpt-4": {
        "provider": g4f.Provider.DDG,
        "model": "gpt-4o-mini",
    },
    "claude-3": {
        "provider": g4f.Provider.DDG,
        "model": "claude-3-haiku",
    },
    "llama-3.1-70b": {
        "provider": g4f.Provider.DDG,
        "model": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
    },
    "mixtral-8x7b": {
        "provider": g4f.Provider.DDG,
        "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
    },
}


def chat_with_model(messages, model_key="gpt-4o-mini"):
    """聊天函数"""
    config = STABLE_MODELS.get(model_key, STABLE_MODELS["gpt-4o-mini"])
    
    try:
        response = g4f.ChatCompletion.create(
            model=config["model"],
            provider=config["provider"],
            messages=messages,
            timeout=60
        )
        return response, config["provider"].__name__
    except Exception as e:
        print(f"Error: {e}")
        # 降级尝试
        try:
            response = g4f.ChatCompletion.create(
                model="gpt-4o-mini",
                provider=g4f.Provider.DDG,
                messages=messages,
                timeout=60
            )
            return response, "DDG_fallback"
        except Exception as e2:
            return str(e2), "error"


@app.route("/v1/chat/completions", methods=["POST"])
def chat_completions():
    data = request.json
    messages = data.get("messages", [])
    model = data.get("model", "gpt-4o-mini")
    stream = data.get("stream", False)
    
    if stream:
        return stream_response(messages, model)
    
    response, provider_used = chat_with_model(messages, model)
    
    return jsonify({
        "id": "chatcmpl-xxx",
        "object": "chat.completion",
        "model": model,
        "provider": provider_used,
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": response
            },
            "finish_reason": "stop"
        }]
    })


def stream_response(messages, model_key):
    """流式响应"""
    def generate():
        config = STABLE_MODELS.get(model_key, STABLE_MODELS["gpt-4o-mini"])
        
        try:
            response = g4f.ChatCompletion.create(
                model=config["model"],
                provider=config["provider"],
                messages=messages,
                stream=True,
                timeout=120
            )
            
            for chunk in response:
                if chunk:
                    data = {
                        "id": "chatcmpl-xxx",
                        "object": "chat.completion.chunk",
                        "model": model_key,
                        "choices": [{
                            "index": 0,
                            "delta": {"content": chunk},
                            "finish_reason": None
                        }]
                    }
                    yield f"data: {json.dumps(data)}\n\n"
            
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')


@app.route("/v1/models", methods=["GET"])
def list_models():
    models = [{"id": m, "object": "model", "owned_by": "g4f"} for m in STABLE_MODELS.keys()]
    return jsonify({"object": "list", "data": models})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "models": list(STABLE_MODELS.keys())})


@app.route("/providers", methods=["GET"])
def list_providers():
    """列出所有可用的 providers"""
    providers = [p for p in dir(g4f.Provider) if not p.startswith('_')]
    return jsonify({"providers": providers})


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "G4F API is running",
        "endpoints": ["/v1/chat/completions", "/v1/models", "/health", "/providers"]
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860)
