from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import g4f
import json

app = Flask(__name__)
CORS(app)

@app.route("/v1/chat/completions", methods=["POST"])
def chat_completions():
    data = request.json
    messages = data.get("messages", [])
    model = data.get("model", "gpt-4o-mini")
    stream = data.get("stream", False)
    
    if stream:
        return stream_response(messages, model)
    
    try:
        response = g4f.ChatCompletion.create(
            model="gpt-4o-mini",
            provider=g4f.Provider.DDG,
            messages=messages,
            timeout=60
        )
        return jsonify({
            "id": "chatcmpl-xxx",
            "object": "chat.completion",
            "model": model,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": response},
                "finish_reason": "stop"
            }]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def stream_response(messages, model):
    def generate():
        try:
            response = g4f.ChatCompletion.create(
                model="gpt-4o-mini",
                provider=g4f.Provider.DDG,
                messages=messages,
                stream=True
            )
            for chunk in response:
                if chunk:
                    yield f"data: {json.dumps({'choices':[{'delta':{'content':chunk}}]})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    return Response(generate(), mimetype='text/event-stream')


@app.route("/v1/models", methods=["GET"])
def list_models():
    return jsonify({"data": [{"id": "gpt-4o-mini"}]})


@app.route("/health")
def health():
    return "OK"


@app.route("/")
def home():
    return "G4F API Running"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860)
