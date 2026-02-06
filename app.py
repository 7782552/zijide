import os
import sys

# 在导入 g4f 之前设置所有环境变量和目录
os.environ["G4F_DIR"] = "/tmp/g4f"
os.environ["HAR_DIR"] = "/tmp/har_and_cookies"
os.environ["G4F_PROXY"] = ""

# 创建必要的目录
for dir_path in ["/tmp/g4f", "/tmp/har_and_cookies", "/app/har_and_cookies"]:
    os.makedirs(dir_path, exist_ok=True)
    try:
        os.chmod(dir_path, 0o777)
    except:
        pass

# 现在导入 g4f
import g4f
from g4f.client import Client
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# 初始化 g4f 客户端
client = Client()

@app.route("/")
def index():
    try:
        models = [m for m in dir(g4f.models) if not m.startswith("_")]
        return f"""
        <h1>🚀 G4F API Online</h1>
        <h3>Status: Running</h3>
        <h3>Available Models ({len(models)}):</h3>
        <p>{', '.join(models[:30])}...</p>
        <h3>Usage:</h3>
        <pre>
POST /v1/chat/completions
{{
    "model": "gpt-4o-mini",
    "messages": [{{"role": "user", "content": "Hello"}}]
}}
        </pre>
        """
    except Exception as e:
        return f"<h1>API Online</h1><p>Error: {e}</p>"

@app.route("/v1/chat/completions", methods=["POST"])
def chat():
    try:
        data = request.json
        messages = data.get("messages", [])
        model = data.get("model", "gpt-4o-mini")
        
        # 使用新的 Client API
        response = client.chat.completions.create(
            model=model,
            messages=messages
        )
        
        # 提取回复内容
        content = response.choices[0].message.content
        
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
        # 备用方案：使用旧 API
        try:
            response = g4f.ChatCompletion.create(
                model=model,
                messages=messages,
                stream=False
            )
            return jsonify({
                "id": "chatcmpl-g4f",
                "object": "chat.completion",
                "model": model,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": str(response)
                    },
                    "finish_reason": "stop"
                }]
            })
        except Exception as e2:
            return jsonify({
                "error": {
                    "message": f"Primary error: {str(e)}, Fallback error: {str(e2)}",
                    "type": "api_error"
                }
            }), 500

@app.route("/v1/models", methods=["GET"])
def list_models():
    models = [m for m in dir(g4f.models) if not m.startswith("_")]
    return jsonify({
        "data": [{"id": m, "object": "model"} for m in models]
    })

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
