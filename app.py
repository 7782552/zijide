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
    return "<h1>G4F Top Models API</h1><p>Status: Running</p>"

@app.route("/health")
def health():
    return "OK"

@app.route("/v1/models", methods=["GET"])
def models():
    return jsonify({"models": ["gpt-4o", "claude-3.5-sonnet", "claude-3-haiku", "deepseek-chat"]})

@app.route("/v1/chat/completions", methods=["POST"])
def chat():
    data = request.json
    messages = data.get("messages")
    model = data.get("model", "gpt-4o")
    
    # --- 尝试 1: Claude 3.5 Sonnet ---
    try:
        from g4f.Provider import PollinationsAI
        response = g4f.ChatCompletion.create(
            model="claude-3.5-sonnet",
            provider=PollinationsAI,
            messages=messages,
            stream=False
        )
        if response and "error" not in str(response).lower():
            return jsonify({"choices": [{"message": {"role": "assistant", "content": str(response)}}], "model": "claude-3.5-sonnet"})
    except:
        pass

    # --- 尝试 2: Claude 3 Haiku ---
    try:
        from g4f.Provider import DuckDuckGo
        response = g4f.ChatCompletion.create(
            model="claude-3-haiku", 
            provider=DuckDuckGo,
            messages=messages,
            stream=False
        )
        if response and "error" not in str(response).lower():
            return jsonify({"choices": [{"message": {"role": "assistant", "content": str(response)}}], "model": "claude-3-haiku"})
    except:
        pass

    # --- 尝试 3: GPT-4o ---
    try:
        from g4f.Provider import PollinationsAI
        response = g4f.ChatCompletion.create(
            model="gpt-4o",
            provider=PollinationsAI,
            messages=messages,
            stream=False
        )
        if response and "error" not in str(response).lower():
            return jsonify({"choices": [{"message": {"role": "assistant", "content": str(response)}}], "model": "gpt-4o"})
    except:
        pass

    # --- 尝试 4: GPT-4o 保底 ---
    try:
        response = g4f.ChatCompletion.create(
            model="gpt-4o",
            messages=messages,
            stream=False
        )
        return jsonify({"choices": [{"message": {"role": "assistant", "content": str(response)}}], "model": "gpt-4o-fallback"})
    except Exception as e:
        return jsonify({"error": f"所有模型均失效: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
