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
    return "<h1>GPT-5 API</h1><p>Working!</p>"

@app.route("/health")
def health():
    return "OK"

@app.route("/v1/chat/completions", methods=["POST"])
def chat():
    try:
        data = request.json
        messages = data.get("messages", [])
        
        # 只用 Chatgpt4Online
        from g4f.Provider import Chatgpt4Online
        response = g4f.ChatCompletion.create(
            model="gpt-4",
            provider=Chatgpt4Online,
            messages=messages,
            stream=False,
            timeout=120
        )
        
        return jsonify({
            "choices": [{"message": {"role": "assistant", "content": str(response)}}],
            "model": "gpt-5",
            "provider": "Chatgpt4Online"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
