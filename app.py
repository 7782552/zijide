import os
import sys

# 设置环境变量
os.environ["G4F_DIR"] = "/tmp/g4f"
os.environ["G4F_NO_GUI"] = "1"

# 创建目录
for d in ["/tmp/g4f", "/tmp/har_and_cookies"]:
    os.makedirs(d, exist_ok=True)

from flask import Flask, request, jsonify
from flask_cors import CORS
import g4f
from g4f.Provider import __all__ as all_providers
import g4f.Provider as Provider

app = Flask(__name__)
CORS(app)

def get_working_providers():
    """动态获取所有可用的 Provider"""
    working = []
    for provider_name in all_providers:
        try:
            provider = getattr(Provider, provider_name, None)
            if provider and hasattr(provider, 'create_completion'):
                # 检查是否需要认证
                needs_auth = getattr(provider, 'needs_auth', False)
                if not needs_auth:
                    working.append(provider)
        except:
            continue
    return working

def get_response(messages, model="gpt-4o-mini"):
    """尝试多个 Provider 直到成功"""
    
    errors = []
    providers = get_working_providers()
    
    # 优先尝试这些通常稳定的 provider
    priority_names = [
        'DDG', 'Blackbox', 'Pizzagpt', 'Koala', 
        'FreeChatgpt', 'FreeGpt', 'Liaobots',
        'ChatgptFree', 'DeepInfra', 'Phind',
        'You', 'Bing', 'HuggingChat'
    ]
    
    # 按优先级排序
    sorted_providers = []
    for name in priority_names:
        for p in providers:
            if p.__name__ == name:
                sorted_providers.append(p)
                break
    
    # 添加其他 provider
    for p in providers:
        if p not in sorted_providers:
            sorted_providers.append(p)
    
    for provider in sorted_providers[:15]:  # 最多尝试15个
        try:
            response = g4f.ChatCompletion.create(
                model=model,
                messages=messages,
                provider=provider,
                stream=False,
                timeout=30
            )
            if response and str(response).strip():
                return str(response), provider.__name__
        except Exception as e:
            error_msg = str(e)[:80]
            errors.append(f"{provider.__name__}: {error_msg}")
            continue
    
    raise Exception(f"All providers failed. Tried: {', '.join([p.__name__ for p in sorted_providers[:10]])}")

@app.route("/")
def index():
    providers = get_working_providers()
    provider_names = [p.__name__ for p in providers]
    
    return f"""
    <html>
    <head><title>G4F API</title></head>
    <body>
        <h1>🚀 G4F API Online</h1>
        <h3>Status: Running</h3>
        <h3>Available Providers ({len(providers)}):</h3>
        <p>{', '.join(sorted(provider_names))}</p>
        <hr>
        <h3>Test Endpoint:</h3>
        <p><a href="/test">/test</a> - Quick API test</p>
        <h3>Usage:</h3>
        <pre>
POST /v1/chat/completions
Content-Type: application/json

{{
    "model": "gpt-4o-mini",
    "messages": [
        {{"role": "user", "content": "Hello"}}
    ]
}}
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
    models = ["gpt-4o-mini", "gpt-4o", "gpt-4", "gpt-3.5-turbo", "claude-3-sonnet"]
    return jsonify({
        "data": [{"id": m, "object": "model"} for m in models]
    })

@app.route("/providers", methods=["GET"])
def list_providers():
    providers = get_working_providers()
    return jsonify({
        "count": len(providers),
        "providers": [p.__name__ for p in providers]
    })

@app.route("/test")
def test():
    try:
        content, provider = get_response(
            [{"role": "user", "content": "Say hello in one word"}],
            "gpt-4o-mini"
        )
        return jsonify({
            "status": "success",
            "provider": provider,
            "response": content[:200]
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
