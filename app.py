from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import g4f
import json

app = Flask(__name__)
CORS(app)

# ✅ 稳定模型配置
STABLE_MODELS = {
    "deepseek": {
        "provider": g4f.Provider.DeepSeek,
        "model": "deepseek-chat",
    },
    "deepseek-r1": {
        "provider": g4f.Provider.DeepSeekV3,
        "model": "deepseek-reasoner",
    },
    "gpt-4": {
        "provider": g4f.Provider.Liaobots,
        "model": "gpt-4-turbo",
    },
    "gpt-4o": {
        "provider": g4f.Provider.ChatGptEs,
        "model": "gpt-4o",
    },
    "gpt-4o-mini": {
        "provider": g4f.Provider.DDG,
        "model": "gpt-4o-mini",
    },
    "claude-3.5-sonnet": {
        "provider": g4f.Provider.Liaobots,
        "model": "claude-3.5-sonnet",
    },
    "llama-3.1-70b": {
        "provider": g4f.Provider.DDG,
        "model": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
    },
    "mixtral-8x7b": {
        "provider": g4f.Provider.DDG,
        "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
    },
    "qwen-2-72b": {
        "provider": g4f.Provider.HuggingChat,
        "model": "Qwen/Qwen2.5-72B-Instruct",
    },
}

# 备用 Provider
FALLBACK_PROVIDERS = [
    g4f.Provider.DDG,
    g4f.Provider.ChatGptEs,
    g4f.Provider.Liaobots,
    g4f.Provider.FreeChatgpt,
    g4f.Provider.You,
]


def chat_with_fallback(messages, model_key="gpt-4o-mini"):
    """带自动降级的聊天函数"""
    
    if model_key in STABLE_MODELS:
        config = STABLE_MODELS[model_key]
        try:
            response = g4f.ChatCompletion.create(
                model=config["model"],
                provider=config["provider"],
                messages=messages,
                timeout=60
            )
            return response, config["provider"].__name__
        except Exception as e:
            print(f"Primary provider failed: {e}")
    
    for provider in FALLBACK_PROVIDERS:
        try:
            response = g4f.ChatCompletion.create(
                model="gpt-4o-mini",
                provider=provider,
                messages=messages,
                timeout=60
            )
            return response, provider.__name__
        except Exception as e:
            print(f"{provider.__name__} failed: {e}")
            continue
    
    return None, "all_failed"


@app.route("/v1/chat/completions", methods=["POST"])
def chat_completions():
    data = request.json
    messages = data.get("messages", [])
    model = data.get("model", "gpt-4o-mini")
    stream = data.get("stream", False)
    
    if stream:
        return stream_response(messages, model)
    
    response, provider_used = chat_with_fallback(messages, model)
    
    if response is None:
        return jsonify({"error": "All providers failed"}), 503
    
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
        config = STABLE_MODELS.get(model_key, {
            "provider": g4f.Provider.DDG,
            "model": "gpt-4o-mini"
        })
        
        try:
            response = g4f.ChatCompletion.create(
                model=config.get("model", model_key),
                provider=config.get("provider"),
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
    """列出可用模型"""
    models = []
    for model_id in STABLE_MODELS.keys():
        models.append({
            "id": model_id,
            "object": "model",
            "owned_by": "g4f"
        })
    return jsonify({"object": "list", "data": models})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "models": list(STABLE_MODELS.keys())})


@app.route("/test", methods=["GET"])
def test_providers():
    """测试所有 Provider 的可用性"""
    results = {}
    test_messages = [{"role": "user", "content": "Say 'OK' only"}]
    
    for name, config in STABLE_MODELS.items():
        try:
            response = g4f.ChatCompletion.create(
                model=config["model"],
                provider=config["provider"],
                messages=test_messages,
                timeout=30
            )
            results[name] = {"status": "✅", "response": response[:50] if response else "empty"}
        except Exception as e:
            results[name] = {"status": "❌", "error": str(e)[:100]}
    
    return jsonify(results)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860)
