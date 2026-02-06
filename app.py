import os
import sys

# 设置环境变量（必须在导入 g4f 之前）
os.environ["G4F_DIR"] = "/tmp/g4f"
os.environ["G4F_NO_GUI"] = "1"
os.environ["CHROME_PATH"] = "/usr/bin/chromium"

# 创建目录
for d in ["/tmp/g4f", "/tmp/har_and_cookies"]:
    os.makedirs(d, exist_ok=True)

from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def get_response(messages, model="gpt-4o-mini"):
    """尝试多个免费 Provider"""
    import g4f
    
    # 不需要 har 文件的免费 Providers 列表
    free_providers = [
        g4f.Provider.Free2GPT,
        g4f.Provider.FreeGpt,
        g4f.Provider.Koala,
        g4f.Provider.ChatgptFree,
        g4f.Provider.DDG,  # DuckDuckGo
        g4f.Provider.Pizzagpt,
        g4f.Provider.Liaobots,
        g4f.Provider.FreeChatgpt,
        g4f.Provider.DeepInfra,
        g4f.Provider.Blackbox,
    ]
    
    errors = []
    
    for provider in free_providers:
        try:
            response = g4f.ChatCompletion.create(
                model=model,
                messages=messages,
                provider=provider,
                stream=False,
                timeout=60
            )
            if response and str(response).strip():
                return str(response), provider.__name__
        except Exception as e:
            errors.append(f"{provider.__name__}: {str(e)[:50]}")
            continue
    
    # 最后尝试自动选择
    try:
        response = g4f.ChatCompletion.create(
            model=model,
            messages=messages,
            stream=False
        )
        if response:
            return str(response), "auto"
    except Exception as e:
        errors.append(f"auto: {str(e)[:50]}")
    
    raise Exception(f"All providers failed: {'; '.join(errors[:5])}")

@app.route("/")
def index():
    import g4f
    
    # 列出可用的 providers
    providers = []
    for name in dir(g4f.Provider):
        if not name.startswith("_"):
            providers.append(name)
    
    return f"""
    <html>
    <head><title>G4F API</title></head>
    <body>
        <h1>🚀 G4F API Online</h1>
        <h3>Status: Running</h3>
        <h3>Providers ({len(providers)}):</h3>
        <p style="word-wrap: break-word;">{', '.join(sorted(providers)[:40])}...</p>
        <h3>Usage Example:</h3>
        <pre>
curl -X POST {request.url_root}v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -d '{{"model":"gpt-4o-mini","messages":[{{"role":"user","content":"Hello"}}]}}'
        </pre>
    </body>
    </html>
    """

@app.route("/v1/chat/completions", methods=["POST"])
def chat():
    try:
        data = request.json or {}
        messages = data.get("messages", [])
        model = data.get("model", "gpt-4o-mini")
        
        if not messages:
            return jsonify({"error": "messages is required"}), 400
        
        content, provider_used = get_response(messages, model)
        
        return jsonify({
            "id": "chatcmpl-g4f",
            "object": "chat.completion",
            "model": model,
            "provider": provider_used,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content
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
    models = [
        "gpt-4o-mini",
        "gpt-4o", 
        "gpt-4",
        "gpt-3.5-turbo",
        "claude-3-sonnet",
        "llama-3-70b",
        "mixtral-8x7b"
    ]
    return jsonify({
        "data": [{"id": m, "object": "model"} for m in models]
    })

@app.route("/health")
def health():
    return jsonify({"status": "healthy"})

# 测试端点
@app.route("/test")
def test():
    try:
        content, provider = get_response([{"role": "user", "content": "Say OK"}])
        return jsonify({
            "status": "success",
            "provider": provider,
            "response": content[:100]
        })
    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": str(e)
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
