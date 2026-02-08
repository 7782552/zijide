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
        # 不指定 provider，让 g4f 自动选择
        response = g4f.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=messages
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


@app.route("/providers")
def providers():
    # 列出所有可用的 provider
    p = [x for x in dir(g4f.Provider) if not x.startswith('_')]
    return jsonify({"providers": p})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860)
