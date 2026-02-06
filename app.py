import os

os.environ["G4F_DIR"] = "/tmp/g4f"
os.environ["G4F_NO_GUI"] = "1"
os.makedirs("/tmp/g4f", exist_ok=True)

from flask import Flask, request, jsonify
from flask_cors import CORS
import g4f
import g4f.Provider as Provider

app = Flask(__name__)
CORS(app)

# 只用最快的 Provider
FAST_PROVIDERS = [
    ("DDG", "gpt-4o-mini"),           # DuckDuckGo - 最快
    ("Blackbox", "blackboxai"),        # Blackbox - 快速
    ("Pizzagpt", "gpt-4o-mini"),       # 备用
]

def get_response(messages, model="gpt-4o-mini"):
    """快速获取响应 - 只尝试3个最快的Provider"""
    
    errors = []
    
    for provider_name, default_model in FAST_PROVIDERS:
        try:
            provider = getattr(Provider, provider_name, None)
            if not provider:
                continue
            
            response = g4f.ChatCompletion.create(
                model=model if model else default_model,
                messages=messages,
                provider=provider,
                stream=False,
                timeout=20  # 20秒超时
            )
            
            result = str(response).strip()
            
            # 简单验证
            if result and len(result) > 2 and "not found" not in result.lower():
                return result, provider_name
                
        except Exception as e:
            errors.append(f"{provider_name}: {str(e)[:30]}")
            continue
    
    raise Exception(f"Failed: {'; '.join(errors)}")

@app.route("/")
def index():
    return """
    <h1>🚀 G4F Fast API</h1>
    <p>快速 AI API</p>
    <ul>
        <li><a href="/test">测试</a></li>
        <li>POST /v1/chat/completions</li>
    </ul>
    """

@app.route("/v1/chat/completions", methods=["POST"])
def chat():
    try:
        data = request.json or {}
        messages = data.get("messages", [])
        model = data.get("model", "gpt-4o-mini")
        
        if not messages:
            return jsonify({"error": "messages required"}), 400
        
        content, provider = get_response(messages, model)
        
        return jsonify({
            "id": "chatcmpl-g4f",
            "object": "chat.completion", 
            "model": model,
            "provider": provider,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop"
            }]
        })
        
    except Exception as e:
        return jsonify({"error": {"message": str(e)}}), 500

@app.route("/test")
def test():
    try:
        content, provider = get_response(
            [{"role": "user", "content": "说你好"}],
            "gpt-4o-mini"
        )
        return jsonify({
            "status": "ok",
            "provider": provider,
            "response": content[:200]
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/health")
def health():
    return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
