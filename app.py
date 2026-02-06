import os
import g4f
from flask import Flask, request, jsonify
from flask_cors import CORS

os.environ["G4F_DIR"] = "/tmp/g4f"
os.makedirs("/tmp/g4f", mode=0o777, exist_ok=True)

app = Flask(__name__)
CORS(app)

@app.route("/")
def index():
    return jsonify({"status": "online", "message": "G4F API is running!"})

@app.route("/health")
def health():
    return "OK"

@app.route("/v1/chat/completions", methods=["POST"])
def chat():
    try:
        data = request.json
        messages = data.get("messages", [])
        
        response = g4f.ChatCompletion.create(
            model=g4f.models.default,
            messages=messages,
            stream=False
        )
        
        return jsonify({
            "choices": [{
                "message": {
                    "role": "assistant", 
                    "content": str(response)
                }
            }]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("Server starting on port 7860...")
    app.run(host="0.0.0.0", port=7860, debug=True)
