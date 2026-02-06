import os
import sys
import re

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

# 错误响应关键词
ERROR_KEYWORDS = [
    "does not exist",
    "not available", 
    "error",
    "failed",
    "unable to",
    "invalid",
    "unauthorized",
    "forbidden",
    "rate limit",
    "timeout",
    "not found",
]

# 需要过滤的广告内容
AD_PATTERNS = [
    r"https?://llmplayground\.net",
    r"Want best roleplay experience\?",
    r"https?://[^\s]+playground[^\s]*",
]

def clean_response(response):
    """清理响应中的广告内容"""
    cleaned = str(response)
    
    for pattern in AD_PATTERNS:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
    
    # 清理多余的空行
    cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)
    cleaned = cleaned.strip()
    
    return cleaned

def is_valid_response(response):
    """检查响应是否有效"""
    if not response:
        return False
    
    response_lower = str(response).lower()
    
    for keyword in ERROR_KEYWORDS:
        if keyword in response_lower:
            return False
    
    if len(str(response).strip()) < 3:
        return False
    
    return True

def get_working_providers():
    """获取可用的 Provider"""
    
    excluded = [
        'Retry', 'Base', 'BaseProvider', 
        'AsyncProvider', 'CreateImagesProvider',
    ]
    
    working = []
    for provider_name in all_providers:
        if provider_name in excluded:
            continue
        try:
            provider = getattr(Provider, provider_name, None)
            if provider and hasattr(provider, 'create_completion'):
                needs_auth = getattr(provider, 'needs_auth', False)
                if not needs_auth:
                    working.append(provider)
        except:
            continue
    return working

def get_response(messages, model="gpt-3.5-turbo"):
    """尝试多个 Provider"""
    
    errors = []
    providers = get_working_providers()
    
    # 优先级排序（ApiAirforce 放后面因为有广告）
    priority_names = [
        'DDG',
        'Blackbox',
        'Phind',
        'Pizzagpt',
        'FreeChatgpt',
        'Koala',
        'FreeGpt',
        'ChatgptFree',
        'DeepInfra',
        'HuggingChat',
        'Liaobots',
        'You',
        'ApiAirforce',  # 放后面，因为有广告
    ]
    
    sorted_providers = []
    for name in priority_names:
        for p in providers:
            if p.__name__ == name:
                sorted_providers.append(p)
                break
    
    for p in providers:
        if p not in sorted_providers:
            sorted_providers.append(p)
    
    model_variants = [model, "gpt-3.5-turbo", "gpt-4o-mini", ""]
    
    for provider in sorted_providers[:12]:
        for try_model in model_variants[:2]:
            try:
                response = g4f.ChatCompletion.create(
                    model=try_model if try_model else None,
                    messages=messages,
                    provider=provider,
                    stream=False,
                    timeout=30
                )
                
                response_str = str(response).strip()
                
                if is_valid_response(response_str):
                    # 清理广告
                    cleaned = clean_response(response_str)
                    if cleaned:
                        return cleaned, provider.__name__, try_model or "default"
                    
            except Exception as e:
                errors.append(f"{provider.__name__}: {str(e)[:50]}")
                continue
    
    raise Exception(f"All providers failed")

@app.route("/")
def index():
    providers = get_working_providers()
    
    return f"""
    <html>
    <head><title>G4F API</title></head>
    <body>
        <h1>🚀 G4F API Online</h1>
        <h3>Status: Running ✅</h3>
        <p>Providers: {len(providers)} available</p>
        <hr>
        <h3>Quick Test:</h3>
        <p><a href="/test">/test</a></p>
        <h3>Chat API:</h3>
        <pre>
POST /v1/chat/completions
{{
    "messages": [{{"role": "user", "content": "Hello"}}]
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
        model = data.get("model", "gpt-3.5-turbo")
        
        if not messages:
            return jsonify({"error": "messages is required"}), 400
        
        content, provider_used, model_used = get_response(messages, model)
        
        return jsonify({
            "id": "chatcmpl-g4f",
            "object": "chat.completion",
            "model": model_used,
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
    models = ["gpt-3.5-turbo", "gpt-4o-mini", "gpt-4o", "gpt-4"]
    return jsonify({
        "data": [{"id": m, "object": "model"} for m in models]
    })

@app.route("/providers")
def list_providers():
    providers = get_working_providers()
    return jsonify({
        "count": len(providers),
        "providers": sorted([p.__name__ for p in providers])
    })

@app.route("/test")
def test():
    try:
        content, provider, model = get_response(
            [{"role": "user", "content": "用中文说你好"}],
            "gpt-3.5-turbo"
        )
        return jsonify({
            "status": "success",
            "provider": provider,
            "model": model,
            "response": content
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
