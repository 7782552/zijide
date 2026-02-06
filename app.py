FROM python:3.10-slim

RUN apt-get update && apt-get install -y gcc python3-dev && rm -rf /var/lib/apt/lists/*
# 锁定版本 0.3.3.0 是为了保证 Provider 的稳定性
RUN pip install --no-cache-dir g4f==0.3.3.0 flask flask-cors

WORKDIR /app

RUN cat <<EOF > app.py
import os
import g4f
from flask import Flask, request, jsonify
from flask_cors import CORS

os.environ["G4F_DIR"] = "/tmp/g4f"
if not os.path.exists("/tmp/g4f"):
    os.makedirs("/tmp/g4f", mode=0o777)

app = Flask(__name__)
CORS(app)

def gpt4_fallback(messages):
    """保底函数，确保 Claude 失败时能用 GPT-4 出字"""
    try:
        response = g4f.ChatCompletion.create(
            model="gpt-4o",
            messages=messages,
            stream=False
        )
        return jsonify({"choices": [{"message": {"role": "assistant", "content": str(response)}}], "model": "gpt-4-fallback"})
    except Exception as e:
        return jsonify({"error": f"所有模型均失效: {str(e)}"}), 200

@app.route("/")
def index():
    return "<h1>Claude Sniper v2</h1><p>Status: Running</p>"

@app.route("/v1/chat/completions", methods=["POST"])
def chat():
    data = request.json
    messages = data.get("messages")
    
    # --- 尝试 1: DuckDuckGo (目前 Claude 3 Haiku 最稳的通道) ---
    try:
        from g4f.Provider import DuckDuckGo
        response = g4f.ChatCompletion.create(
            model="claude-3-haiku", 
            provider=DuckDuckGo,
            messages=messages,
            stream=False
        )
        if response and "error" not in str(response).lower():
            return jsonify({"choices": [{"message": {"role": "assistant", "content": str(response)}}], "model": "claude-haiku-ddg"})
    except:
        pass

    # --- 尝试 2: PollinationsAI (Claude 3.5 Sonnet) ---
    try:
        from g4f.Provider import PollinationsAI
        response = g4f.ChatCompletion.create(
            model="claude-3.5-sonnet",
            provider=PollinationsAI,
            messages=messages,
            stream=False
        )
        return jsonify({"choices": [{"message": {"role": "assistant", "content": str(response)}}], "model": "claude-3.5-pollinations"})
    except:
        pass

    # 如果 Claude 都失败了，执行保底逻辑
    return gpt4_fallback(messages)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860)
EOF

EXPOSE 7860
CMD ["python", "app.py"]      
