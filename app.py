from flask import Flask, request, jsonify
import g4f

app = Flask(__name__)

@app.route("/")
def home():
    return "G4F API"

@app.route("/health")
def health():
    return "OK"

@app.route("/v1/chat/completions", methods=["POST"])
def chat():
    try:
        data = request.json
        messages = data.get("messages", [])
        response = g4f.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=messages
        )
        return jsonify({
            "choices": [{"message": {"content": response}}]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
