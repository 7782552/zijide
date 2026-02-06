FROM python:3.10-slim

RUN apt-get update && apt-get install -y gcc python3-dev curl && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir --upgrade g4f flask flask-cors gunicorn

WORKDIR /app

RUN cat <<'EOF' > app.py
import os
import g4f
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import json

# 设置 g4f 目录
os.environ["G4F_DIR"] = "/tmp/g4f"
os.makedirs("/tmp/g4f", mode=0o777, exist_ok=True)

app = Flask(__name__)
CORS(app)

def get_available_models():
    """获取所有可用模型"""
    models = []
    for name in dir(g4f.models):
        if not name.startswith("_"):
            obj = getattr(g4f.models, name)
            if hasattr(obj, "name"):
                models.append(name)
    return models

def find_working_model(messages, preferred_models=None):
    """尝试找到可用的模型"""
    if preferred_models is None:
        preferred_models = ["gpt_4", "gpt_35_turbo", "claude", "default"]
    
    for model_name in preferred_models:
        try:
            model = getattr(g4f.models, model_name, g4f.models.default)
            response = g4f.ChatCompletion.create(
                model=model,
                messages=messages,
                stream=False
            )
            if response and str(response).strip():
                return str(response), model_name
        except Exception:
            continue
    return None, None

@app.route("/")
def index():
    models = get_available_models()
    return jsonify({
        "status": "online",
        "available_models": models,
        "endpoints": {
            "chat": "/v1/chat/completions",
            "models": "/v1/models"
        }
    })

@app.route("/health")
def health():
    return jsonify({"status": "healthy"})

@app.route("/v1/models", methods=["GET"])
def list_models():
    models = get_available_models()
    return jsonify({
        "object": "list",
        "data": [{"id": m, "object": "model"} for m in models]
    })

@app.route("/v1/chat/completions", methods=["POST"])
def chat():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        messages = data.get("messages")
        if not messages:
            return jsonify({"error": "No messages provided"}), 400
        
        model_name = data.get("model", "default")
        stream = data.get("stream", False)
        
        # 获取模型
        model = getattr(g4f.models, model_name, g4f.models.default)
        
        if stream:
            # 流式响应
            def generate():
                try:
                    response = g4f.ChatCompletion.create(
                        model=model,
                        messages=messages,
                        stream=True
                    )
                    for chunk in response:
                        chunk_data = {
                            "choices": [{
                                "delta": {"content": chunk},
                                "index": 0
                            }]
                        }
                        yield f"data: {json.dumps(chunk_data)}\n\n"
                    yield "data: [DONE]\n\n"
                except Exception as e:
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
            return Response(
                stream_with_context(generate()),
                content_type="text/event-stream"
            )
        else:
            # 非流式响应
            try:
                response = g4f.ChatCompletion.create(
                    model=model,
                    messages=messages,
                    stream=False
                )
                content = str(response)
            except Exception as e:
                # 后备方案：尝试其他模型
                content, used_model = find_working_model(messages)
                if content is None:
                    return jsonify({
                        "error": f"All models failed. Last error: {str(e)}"
                    }), 500
                model_name = used_model
            
            return jsonify({
                "id": "chatcmpl-g4f",
                "object": "chat.completion",
                "model": model_name,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": content
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": -1,
                    "completion_tokens": -1,
                    "total_tokens": -1
                }
            })
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("Starting G4F API Server...")
    print(f"Available models: {get_available_models()}")
    app.run(host="0.0.0.0", port=7860, debug=False)
EOF

EXPOSE 7860

# 使用 gunicorn 生产环境部署
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "--workers", "2", "--timeout", "120", "app:app"]
EOF
