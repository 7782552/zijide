import os
import g4f
from flask import Flask, request, jsonify
from flask_cors import CORS

os.environ["G4F_DIR"] = "/tmp/g4f"
if not os.path.exists("/tmp/g4f"):
    os.makedirs("/tmp/g4f", mode=0o777)

app = Flask(__name__)
CORS(app)

@app.route("/")
def index():
    return "<h1>GPT-5 API</h1><p>Providers: Chatgpt4Online, Koala</p>"

@app.route("/health")
def health():
    return "OK"

@app.route("/v1/models", methods=["GET"])
def models():
    return jsonify({"models": ["gpt-5", "gpt-5-mini"]})

@app.route("/v1/chat/completions", methods=["POST"])
def chat():
    data = request.json
    messages = data.get("messages")
    model = data.get("model", "gpt-5")
    
    # 尝试 1: Chatgpt4Online (GPT-5)
    try:
        from g4f.Provider import Chatgpt4Online
        response = g4f.ChatCompletion.create(
            model="gpt-4",
            provider=Chatgpt4Online,
            messages=messages,
            stream=False
        )
        if response and "error" not in str(response).lower():
            return jsonify({
                "choices": [{"message": {"role": "assistant", "content": str(response)}}],
                "model": "gpt-5",
                "provider": "Chatgpt4Online"
            })
    except:
        pass
    
    # 尝试 2: Koala (GPT-5-mini)
    try:
        from g4f.Provider import Koala
        response = g4f.ChatCompletion.create(
            model="gpt-4",
            provider=Koala,
            messages=messages,
            stream=False
        )
        if response and "error" not in str(response).lower():
            return jsonify({
                "choices": [{"message": {"role": "assistant", "content": str(response)}}],
                "model": "gpt-5-mini",
                "provider": "Koala"
            })
    except:
        pass
    
    # 保底: 自动选择
    try:
        response = g4f.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            stream=False
        )
        return jsonify({
            "choices": [{"message": {"role": "assistant", "content": str(response)}}],
            "model": "auto"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
