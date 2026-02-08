from flask import Flask, request, jsonify
import g4f
import os

# 设置 cookies 目录
os.makedirs("har_and_cookies", exist_ok=True)
os.environ["G4F_HAR_PATH"] = "/app/har_and_cookies"

app = Flask(__name__)

@app.route("/")
def home():
    return "G4F API - Top Models"

@app.route("/health")
def health():
    return "OK"

@app.route("/v1/models", methods=["GET"])
def list_models():
    return jsonify({"models": ["gpt-4o-mini", "gpt-4o", "gpt-4", "claude-3.5-sonnet", "deepseek-chat", "llama-3.1-70b"]})

@app.route("/providers", methods=["GET"])
def list_providers():
    providers = [p for p in dir(g4f.Provider) if not p.startswith('_')]
    return jsonify({"count": len(providers), "providers": providers})

@app.route("/v1/chat/completions", methods=["POST"])
def chat():
    try:
        data = request.json
        messages = data.get("messages", [])
        model = data.get("model", "gpt-4o-mini")
        
        response = g4f.ChatCompletion.create(
            model=model,
            messages=messages,
            ignored=["Bing"]  # 跳过需要登录的
        )
        
        return jsonify({
            "id": "chatcmpl-g4f",
            "model": model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant", 
                    "content": response
                },
                "finish_reason": "stop"
            }]
        })
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
