import os
import g4f
from flask import Flask, request, jsonify
from flask_cors import CORS
import time

os.environ["G4F_DIR"] = "/tmp/g4f"
if not os.path.exists("/tmp/g4f"):
    os.makedirs("/tmp/g4f", mode=0o777)

app = Flask(__name__)
CORS(app)

@app.route("/")
def index():
    return "<h1>GPT API</h1><p>OpenAI Compatible</p>"

@app.route("/health")
def health():
    return "OK"

@app.route("/v1/models", methods=["GET"])
def list_models():
    return jsonify({
        "object": "list",
        "data": [
            {"id": "gpt-4", "object": "model", "owned_by": "openai"},
            {"id": "gpt-4o-mini", "object": "model", "owned_by": "openai"},
        ]
    })

@app.route("/v1/chat/completions", methods=["POST"])
def chat():
    try:
        data = request.json
        messages = data.get("messages", [])
        model = data.get("model", "gpt-4")
        
        response = None
        provider_used = None
        
        # 尝试 1: Koala
        try:
            from g4f.Provider import Koala
            response = g4f.ChatCompletion.create(
                model="gpt-4",
                provider=Koala,
                messages=messages,
                stream=False,
                timeout=60
            )
            if response:
                provider_used = "Koala"
        except:
            pass
        
        # 尝试 2: DuckDuckGo
        if not response:
            try:
                from g4f.Provider import DuckDuckGo
                response = g4f.ChatCompletion.create(
                    model="gpt-4o-mini",
                    provider=DuckDuckGo,
                    messages=messages,
                    stream=False,
                    timeout=60
                )
                if response:
                    provider_used = "DuckDuckGo"
            except:
                pass
        
        # 尝试 3: PollinationsAI
        if not response:
            try:
                from g4f.Provider import PollinationsAI
                response = g4f.ChatCompletion.create(
                    model="gpt-4o",
                    provider=PollinationsAI,
                    messages=messages,
                    stream=False,
                    timeout=60
                )
                if response:
                    provider_used = "PollinationsAI"
            except:
                pass
        
        # 尝试 4: 自动选择
        if not response:
            try:
                response = g4f.ChatCompletion.create(
                    model="gpt-4",
                    messages=messages,
                    stream=False
                )
                if response:
                    provider_used = "Auto"
            except:
                pass
        
        if response:
            return jsonify({
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model,
                "provider": provider_used,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": str(response)
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
            })
        else:
            return jsonify({"error": {"message": "All providers failed", "type": "api_error"}}), 500
        
    except Exception as e:
        return jsonify({"error": {"message": str(e), "type": "api_error"}}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
