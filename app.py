import os
os.environ["G4F_DIR"] = "/tmp/g4f"
os.makedirs("/tmp/g4f", exist_ok=True)

from flask import Flask, request, jsonify
from flask_cors import CORS
import g4f

app = Flask(__name__)
CORS(app)

@app.route("/")
def index():
    return "<h1>✅ G4F API Running</h1><p><a href='/test'>Test API</a></p>"

@app.route("/v1/chat/completions", methods=["POST"])
def chat():
    try:
        data = request.json or {}
        messages = data.get("messages", [])
        model = data.get("model") or "gpt-4o-mini"  # 默认模型
        
        if not messages:
            return jsonify({"error": "messages required"}), 400
        
        # 直接调用，让 g4f 自动选择 provider
        response = g4f.ChatCompletion.create(
            model=model,
            messages=messages,
            stream=False
        )
        
        content = str(response).strip()
        
        return jsonify({
            "id": "chatcmpl-g4f",
            "object": "chat.completion",
            "model": model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }
        })
        
    except Exception as e:
        return jsonify({
            "error": {
                "message": f"Error: {str(e)}",
                "type": "api_error"
            }
        }), 500

@app.route("/v1/models", methods=["GET"])
def models():
    return jsonify({
        "data": [
            {"id": "gpt-4o-mini"},
            {"id": "gpt-4o"},
            {"id": "gpt-4"},
        ]
    })

@app.route("/test")
def test():
    try:
        response = g4f.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "说OK"}],
            stream=False
        )
        return jsonify({
            "status": "success",
            "response": str(response)[:200]
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
