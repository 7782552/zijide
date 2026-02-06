import os
import g4f
from flask import Flask, request, jsonify
from flask_cors import CORS

os.environ["G4F_DIR"] = "/tmp/g4f"
os.makedirs("/tmp/g4f", exist_ok=True)

app = Flask(__name__)
CORS(app)

@app.route("/")
def index():
    try:
        models = [m for m in dir(g4f.models) if not m.startswith("_")]
        return f"""
        <h1>🚀 G4F API Online</h1>
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
        return f"<h1>API Online</h1><p>Error listing models: {e}</p>"

@app.route("/v1/chat/completions", methods=["POST"])
def chat():
    try:
        data = request.json
        messages = data.get("messages", [])
        model = data.get("model", "gpt-4o-mini")
        
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
                "message": str(e),
                "type": "api_error"
            }
        }), 500

@app.route("/v1/models", methods=["GET"])
def list_models():
    models = [m for m in dir(g4f.models) if not m.startswith("_")]
    return jsonify({
        "data": [{"id": m, "object": "model"} for m in models]
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
