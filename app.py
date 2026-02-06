import os
import re
import random

os.environ["G4F_DIR"] = "/tmp/g4f"
os.environ["G4F_NO_GUI"] = "1"

for d in ["/tmp/g4f", "/tmp/har_and_cookies"]:
    os.makedirs(d, exist_ok=True)

from flask import Flask, request, jsonify
from flask_cors import CORS
import g4f
import g4f.Provider as Provider
from g4f.Provider import __all__ as all_providers

app = Flask(__name__)
CORS(app)

# 广告过滤
AD_PATTERNS = [
    r"https?://llmplayground\.net",
    r"Want best roleplay experience\?",
]

def clean_response(response):
    cleaned = str(response)
    for pattern in AD_PATTERNS:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()

def is_valid_response(response):
    if not response or len(str(response).strip()) < 3:
        return False
    
    error_keywords = [
        "does not exist", "not available", "not found",
        "error", "invalid", "unauthorized", "failed",
        "rate limit", "too many requests"
    ]
    response_lower = str(response).lower()
    
    for keyword in error_keywords:
        if keyword in response_lower:
            return False
    return True

def get_all_available_providers():
    """获取所有可用的 Provider"""
    available = []
    excluded = ['Retry', 'Base', 'BaseProvider', 'AsyncProvider', 'CreateImagesProvider']
    
    for name in all_providers:
        if name in excluded:
            continue
        try:
            p = getattr(Provider, name, None)
            if p and hasattr(p, 'create_completion'):
                needs_auth = getattr(p, 'needs_auth', False)
                if not needs_auth:
                    available.append((name, p))
        except:
            pass
    return available

# 模型映射 - 包含多个备选
MODEL_CONFIG = {
    "deepseek-r1": {
        "providers": ["Blackbox", "DeepInfra", "HuggingChat", "Liaobots"],
        "model_names": ["deepseek-r1", "deepseek-reasoner", "deepseek-chat"],
    },
    "deepseek": {
        "providers": ["Blackbox", "DeepInfra"],
        "model_names": ["deepseek-chat", "deepseek-r1"],
    },
    "claude": {
        "providers": ["Blackbox", "Liaobots", "AmigoChat"],
        "model_names": ["claude-sonnet-3.5", "claude-3.5-sonnet", "claude-3-sonnet", "claude"],
    },
    "gpt4": {
        "providers": ["Blackbox", "DDG", "Liaobots", "Pizzagpt", "FreeChatgpt"],
        "model_names": ["gpt-4o", "gpt-4o-mini", "gpt-4", "chatgpt-4o-latest"],
    },
    "gpt3": {
        "providers": ["DDG", "FreeChatgpt", "FreeGpt", "Pizzagpt"],
        "model_names": ["gpt-3.5-turbo", "gpt-4o-mini"],
    },
    "default": {
        "providers": ["Blackbox", "DDG", "Pizzagpt", "FreeChatgpt"],
        "model_names": ["gpt-4o-mini", "gpt-3.5-turbo"],
    }
}

def get_model_config(model):
    """获取模型配置"""
    model_lower = model.lower()
    
    if "deepseek" in model_lower or "r1" in model_lower:
        return MODEL_CONFIG["deepseek-r1"]
    elif "claude" in model_lower:
        return MODEL_CONFIG["claude"]
    elif "gpt-4" in model_lower or "gpt4" in model_lower:
        return MODEL_CONFIG["gpt4"]
    elif "gpt-3" in model_lower or "gpt3" in model_lower:
        return MODEL_CONFIG["gpt3"]
    else:
        return MODEL_CONFIG["default"]

def get_response(messages, model="gpt-4o-mini"):
    """尝试多个 Provider 和模型组合"""
    
    config = get_model_config(model)
    providers = config["providers"]
    model_names = config["model_names"]
    
    errors = []
    
    # 尝试所有 provider 和 model 组合
    for provider_name in providers:
        provider = getattr(Provider, provider_name, None)
        if not provider:
            continue
            
        for try_model in model_names:
            try:
                response = g4f.ChatCompletion.create(
                    model=try_model,
                    messages=messages,
                    provider=provider,
                    stream=False,
                    timeout=45
                )
                
                response_str = str(response).strip()
                
                if is_valid_response(response_str):
                    cleaned = clean_response(response_str)
                    if cleaned and len(cleaned) > 3:
                        return cleaned, provider_name, try_model
                        
            except Exception as e:
                errors.append(f"{provider_name}/{try_model}: {str(e)[:30]}")
                continue
    
    # 最后尝试：使用所有可用 Provider
    all_providers_list = get_all_available_providers()
    random.shuffle(all_providers_list)  # 随机顺序避免总是用同一个
    
    for provider_name, provider in all_providers_list[:10]:
        try:
            response = g4f.ChatCompletion.create(
                model=model_names[0] if model_names else model,
                messages=messages,
                provider=provider,
                stream=False,
                timeout=30
            )
            
            if is_valid_response(str(response)):
                return clean_response(str(response)), provider_name, "fallback"
                
        except:
            continue
    
    raise Exception(f"All providers failed. Last errors: {'; '.join(errors[-3:])}")

@app.route("/")
def index():
    return """
    <html>
    <head>
        <title>G4F API</title>
        <style>
            body { font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px; }
            code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }
            pre { background: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }
            .model { margin: 10px 0; padding: 10px; background: #e8f4e8; border-radius: 5px; }
        </style>
    </head>
    <body>
        <h1>🚀 G4F API</h1>
        <p>免费 AI API - 支持 DeepSeek R1 / Claude / GPT-4</p>
        
        <h2>📋 可用模型</h2>
        <div class="model">🔥 <code>deepseek-r1</code> - DeepSeek R1 推理模型</div>
        <div class="model">🟣 <code>claude-3.5-sonnet</code> - Claude 3.5</div>
        <div class="model">🟢 <code>gpt-4o</code> / <code>gpt-4o-mini</code> - GPT-4</div>
        
        <h2>🧪 测试</h2>
        <ul>
            <li><a href="/test/deepseek">测试 DeepSeek R1</a></li>
            <li><a href="/test/claude">测试 Claude</a></li>
            <li><a href="/test/gpt4">测试 GPT-4</a></li>
            <li><a href="/test/all">测试所有模型</a></li>
        </ul>
        
        <h2>📡 API 使用</h2>
        <pre>
POST /v1/chat/completions
Content-Type: application/json

{
    "model": "deepseek-r1",
    "messages": [
        {"role": "user", "content": "你好"}
    ]
}
        </pre>
        
        <h2>⚠️ 注意</h2>
        <p>这是免费代理服务，可能不稳定。如果一个模型失败，请尝试其他模型。</p>
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
        
        content, provider, actual_model = get_response(messages, model)
        
        return jsonify({
            "id": "chatcmpl-g4f",
            "object": "chat.completion",
            "model": actual_model,
            "provider": provider,
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
        {"id": "deepseek-r1", "name": "DeepSeek R1"},
        {"id": "claude-3.5-sonnet", "name": "Claude 3.5 Sonnet"},
        {"id": "gpt-4o", "name": "GPT-4o"},
        {"id": "gpt-4o-mini", "name": "GPT-4o Mini"},
    ]
    return jsonify({"data": models})

@app.route("/test/<model_type>")
def test_model(model_type):
    model_map = {
        "deepseek": "deepseek-r1",
        "claude": "claude-3.5-sonnet",
        "gpt4": "gpt-4o",
        "gpt": "gpt-4o-mini",
    }
    
    model = model_map.get(model_type, "gpt-4o-mini")
    
    try:
        content, provider, actual_model = get_response(
            [{"role": "user", "content": "你是什么模型？用一句话简短回答。"}],
            model
        )
        return jsonify({
            "status": "success",
            "requested_model": model,
            "actual_model": actual_model,
            "provider": provider,
            "response": content[:500]
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "requested_model": model,
            "message": str(e)
        }), 500

@app.route("/test/all")
def test_all():
    results = {}
    models = ["deepseek-r1", "claude-3.5-sonnet", "gpt-4o"]
    
    for model in models:
        try:
            content, provider, actual = get_response(
                [{"role": "user", "content": "Say OK"}],
                model
            )
            results[model] = {
                "status": "success",
                "provider": provider,
                "response": content[:100]
            }
        except Exception as e:
            results[model] = {
                "status": "error",
                "message": str(e)[:100]
            }
    
    return jsonify(results)

@app.route("/test")
def test_index():
    return """
    <h2>选择测试:</h2>
    <ul>
        <li><a href="/test/deepseek">DeepSeek R1</a></li>
        <li><a href="/test/claude">Claude</a></li>
        <li><a href="/test/gpt4">GPT-4</a></li>
        <li><a href="/test/all">全部测试</a></li>
    </ul>
    """

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

@app.route("/providers")
def list_providers():
    available = get_all_available_providers()
    return jsonify({
        "count": len(available),
        "providers": sorted([name for name, _ in available])
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
