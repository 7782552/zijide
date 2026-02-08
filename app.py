import os
import g4f
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import json
import time

os.environ["G4F_DIR"] = "/tmp/g4f"
if not os.path.exists("/tmp/g4f"):
    os.makedirs("/tmp/g4f", mode=0o777)

app = Flask(__name__)
CORS(app)

@app.route("/")
def index():
    return "<h1>GPT-5 API</h1><p>OpenAI Compatible</p>"

@app.route("/health")
def health():
    return "OK"

# OpenAI 兼容：列出模型
@app.route("/v1/models", methods=["GET"])
def list_models():
    return jsonify({
        "object": "list",
        "data": [
            {"id": "gpt-5", "object": "model", "owned_by": "openai"},
            {"id": "gpt-4", "object": "model", "owned_by": "openai"},
            {"id": "gpt-4o", "object": "model", "owned_by": "openai"},
            {"id": "gpt-3.5-turbo", "object": "model", "owned_by": "openai"},
        ]
    })

# OpenAI 兼容：聊天补全
@app.route("/v1/chat/completions", methods=["POST"])
def chat_completions():
    try:
        data = request.json
        messages = data.get("messages", [])
        model = data.get("model", "gpt-4")
        stream = data.get("stream", False)
        
        # 调用 GPT-5
        from g4f.Provider import Chatgpt4Online
        response = g4f.ChatCompletion.create(
            model="gpt-4",
            provider=Chatgpt4Online,
            messages=messages,
            stream=False,
            timeout=120
        )
        
        response_text = str(response)
        
        # 返回 OpenAI 格式
        return jsonify({
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response_text
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
        return jsonify({"error": {"message": str(e), "type": "api_error"}}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
