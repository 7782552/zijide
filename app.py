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

# 错误响应关键词 - 如果包含这些则认为失败
ERROR_KEYWORDS = [
    "does not exist",
    "not available",
    "error",
    "failed",
    "unable to",
    "cannot",
    "invalid",
    "unauthorized",
    "forbidden",
    "rate limit",
    "timeout",
    "not found",
    "api.airforce",  # 特定错误源
]

def is_valid_response(response):
    """检查响应是否有效"""
    if not response:
        return False
    
    response_lower = str(response).lower()
    
    # 检查是否包含错误关键词
    for keyword in ERROR_KEYWORDS:
        if keyword in response_lower:
            return False
    
    # 响应太短可能是错误
    if len(str(response).strip()) < 5:
        return False
    
    return True

def get_working_providers():
    """获取可用的 Provider，排除已知有问题的"""
    
    # 排除这些有问题的 provider
    excluded = [
        'ApiAirforce',  # 模型不存在错误
        'Retry',
        'Base',
        'BaseProvider', 
        'AsyncProvider',
        'CreateImagesProvider',
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
    """尝试多个 Provider 直到获得有效响应"""
    
    errors = []
    providers = get_working_providers()
    
    # 优先尝试这些稳定的 provider
    priority_names = [
        'DDG',           # DuckDuckGo - 通常稳定
        'Blackbox',      # 通常可用
        'Phind',         # 开发者友好
        'Pizzagpt',      
        'FreeChatgpt',   
        'Koala',
        'FreeGpt',
        'ChatgptFree',
        'DeepInfra',
        'HuggingChat',
        'Liaobots',
        'You',
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
    
    # 尝试不同的模型名称
    model_variants = [
        model,
        "gpt-3.5-turbo",
        "gpt-4o-mini",
        "gpt-4",
        "",  # 让 provider 使用默认模型
    ]
    
    for provider in sorted_providers[:12]:
        for try_model in model_variants[:2]:  # 每个 provider 尝试2个模型
            try:
                response = g4f.ChatCompletion.create(
                    model=try_model if try_model else None,
                    messages=messages,
                    provider=provider,
                    stream=False,
                    timeout=30
                )
                
                response_str = str(response).strip()
                
                # 验证响应是否有效
                if is_valid_response(response_str):
                    return response_str, provider.__name__, try_model or "default"
                else:
                    errors.append(f"{provider.__name__}: Invalid response - {response_str[:50]}")
                    
            except Exception as e:
                errors.append(f"{provider.__name__}: {str(e)[:50]}")
                continue
    
    raise Exception(f"All providers failed. Errors: {'; '.join(errors[:5])}")

@app.route("/")
def index():
    providers = get_working_providers()
    provider_names = [p.__name__ for p in providers]
    
    return f"""
    <html>
    <head><title>G4F API</title></head>
    <body>
        <h1>🚀 G4F API Online</h1>
        <h3>Status: Running ✅</h3>
        <h3>Available Providers ({len(providers)}):</h3>
        <p>{', '.join(sorted(provider_names))}</p>
        <hr>
        <h3>Endpoints:</h3>
        <ul>
            <li><a href="/test">/test</a> - Quick test</li>
            <li><a href="/providers">/providers</a> - List providers</li>
            <li><a href="/health">/health</a> - Health check</li>
        </ul>
        <h3>Chat API:</h3>
        <pre>
POST /v1/chat/completions
Content-Type: application/json

{{
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

@app.route("/providers", methods=["GET"])
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
            [{"role": "user", "content": "Say hi"}],
            "gpt-3.5-turbo"
        )
        return jsonify({
            "status": "success",
            "provider": provider,
            "model": model,
            "response": content[:300]
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
