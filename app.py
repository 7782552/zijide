import os
import re

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
    r"https?://[^\s]+playground[^\s]*",
]

def clean_response(response):
    cleaned = str(response)
    for pattern in AD_PATTERNS:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()

def is_valid_response(response):
    if not response or len(str(response).strip()) < 5:
        return False
    
    error_keywords = ["does not exist", "not available", "error", "invalid", "unauthorized"]
    response_lower = str(response).lower()
    
    for keyword in error_keywords:
        if keyword in response_lower:
            return False
    return True

# 模型和 Provider 配置
MODEL_PROVIDERS = {
    # DeepSeek R1
    "deepseek-r1": [
        ("Blackbox", "deepseek-r1"),
        ("DeepInfra", "deepseek-r1"),
        ("HuggingChat", "deepseek-r1"),
        ("Liaobots", "deepseek-r1"),
    ],
    "deepseek": [
        ("Blackbox", "deepseek-chat"),
        ("DeepInfra", "deepseek-chat"),
    ],
    
    # Claude
    "claude-3.5-sonnet": [
        ("Blackbox", "claude-sonnet-3.5"),
        ("Liaobots", "claude-3.5-sonnet"),
    ],
    "claude-3-opus": [
        ("Liaobots", "claude-3-opus"),
    ],
    "claude": [
        ("Blackbox", "claude-sonnet-3.5"),
        ("Liaobots", "claude-3.5-sonnet"),
    ],
    
    # GPT-4
    "gpt-4o": [
        ("Blackbox", "gpt-4o"),
        ("Liaobots", "gpt-4o"),
        ("DDG", "gpt-4o-mini"),
    ],
    "gpt-4": [
        ("Blackbox", "gpt-4o"),
        ("Liaobots", "gpt-4"),
        ("DDG", "gpt-4o-mini"),
    ],
    "gpt-4o-mini": [
        ("DDG", "gpt-4o-mini"),
        ("Blackbox", "gpt-4o"),
        ("Pizzagpt", "gpt-4o-mini"),
    ],
}

def get_providers_for_model(model):
    """根据模型名获取对应的 Provider 列表"""
    model_lower = model.lower()
    
    # 精确匹配
    if model_lower in MODEL_PROVIDERS:
        return MODEL_PROVIDERS[model_lower]
    
    # 模糊匹配
    if "deepseek" in model_lower or "r1" in model_lower:
        return MODEL_PROVIDERS["deepseek-r1"]
    if "claude" in model_lower:
        return MODEL_PROVIDERS["claude"]
    if "gpt-4o-mini" in model_lower:
        return MODEL_PROVIDERS["gpt-4o-mini"]
    if "gpt-4" in model_lower or "gpt4" in model_lower:
        return MODEL_PROVIDERS["gpt-4"]
    
    # 默认返回所有主要 Provider
    return [
        ("Blackbox", model),
        ("DDG", "gpt-4o-mini"),
        ("Liaobots", model),
        ("DeepInfra", model),
    ]

def get_response(messages, model="deepseek-r1"):
    """获取 AI 响应"""
    
    providers_to_try = get_providers_for_model(model)
    errors = []
    
    for provider_name, provider_model in providers_to_try:
        try:
            provider = getattr(Provider, provider_name, None)
            if not provider:
                continue
            
            response = g4f.ChatCompletion.create(
                model=provider_model,
                messages=messages,
                provider=provider,
                stream=False,
                timeout=60
            )
            
            response_str = str(response).strip()
            
            if is_valid_response(response_str):
                cleaned = clean_response(response_str)
                if cleaned:
                    return cleaned, provider_name, provider_model
                    
        except Exception as e:
            errors.append(f"{provider_name}({provider_model}): {str(e)[:40]}")
            continue
    
    # 最后尝试自动模式
    try:
        response = g4f.ChatCompletion.create(
            model=model,
            messages=messages,
            stream=False,
            timeout=60
        )
        if is_valid_response(str(response)):
            return clean_response(str(response)), "auto", model
    except Exception as e:
        errors.append(f"auto: {str(e)[:40]}")
    
    raise Exception(f"All failed: {'; '.join(errors[:4])}")

@app.route("/")
def index():
    return """
    <html>
    <head><title>G4F API - DeepSeek/Claude/GPT-4</title></head>
    <body>
        <h1>🚀 G4F API Online</h1>
        <h2>支持的模型:</h2>
        <h3>🔥 DeepSeek R1 (推荐)</h3>
        <ul>
            <li><code>deepseek-r1</code> - DeepSeek R1 推理模型</li>
            <li><code>deepseek-chat</code> - DeepSeek Chat</li>
        </ul>
        
        <h3>🟣 Claude</h3>
        <ul>
            <li><code>claude-3.5-sonnet</code></li>
            <li><code>claude-3-opus</code></li>
        </ul>
        
        <h3>🟢 GPT-4</h3>
        <ul>
            <li><code>gpt-4o</code></li>
            <li><code>gpt-4o-mini</code></li>
            <li><code>gpt-4</code></li>
        </ul>
        
        <hr>
        <h3>测试:</h3>
        <ul>
            <li><a href="/test/deepseek">/test/deepseek</a> - 测试 DeepSeek R1</li>
            <li><a href="/test/claude">/test/claude</a> - 测试 Claude</li>
            <li><a href="/test/gpt4">/test/gpt4</a> - 测试 GPT-4</li>
        </ul>
        
        <h3>API 使用:</h3>
        <pre>
POST /v1/chat/completions
{
    "model": "deepseek-r1",
    "messages": [{"role": "user", "content": "你好"}]
}
        </pre>
    </body>
    </html>
    """

@app.route("/v1/chat/completions", methods=["POST"])
def chat():
    try:
        data = request.json or {}
        messages = data.get("messages", [])
        model = data.get("model", "deepseek-r1")
        
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
        {"id": "deepseek-chat", "name": "DeepSeek Chat"},
        {"id": "claude-3.5-sonnet", "name": "Claude 3.5 Sonnet"},
        {"id": "claude-3-opus", "name": "Claude 3 Opus"},
        {"id": "gpt-4o", "name": "GPT-4o"},
        {"id": "gpt-4o-mini", "name": "GPT-4o Mini"},
        {"id": "gpt-4", "name": "GPT-4"},
    ]
    return jsonify({"data": models})

@app.route("/test/deepseek")
def test_deepseek():
    try:
        content, provider, model = get_response(
            [{"role": "user", "content": "你是什么模型？简短回答"}],
            "deepseek-r1"
        )
        return jsonify({
            "status": "success",
            "provider": provider,
            "model": model,
            "response": content[:500]
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/test/claude")
def test_claude():
    try:
        content, provider, model = get_response(
            [{"role": "user", "content": "你是什么模型？简短回答"}],
            "claude-3.5-sonnet"
        )
        return jsonify({
            "status": "success",
            "provider": provider,
            "model": model,
            "response": content[:500]
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/test/gpt4")
def test_gpt4():
    try:
        content, provider, model = get_response(
            [{"role": "user", "content": "你是什么模型？简短回答"}],
            "gpt-4o"
        )
        return jsonify({
            "status": "success",
            "provider": provider,
            "model": model,
            "response": content[:500]
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/test")
def test():
    return """
    <h1>选择测试模型:</h1>
    <ul>
        <li><a href="/test/deepseek">DeepSeek R1</a></li>
        <li><a href="/test/claude">Claude 3.5</a></li>
        <li><a href="/test/gpt4">GPT-4o</a></li>
    </ul>
    """

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

@app.route("/providers")
def list_providers():
    available = []
    for name in all_providers:
        try:
            p = getattr(Provider, name, None)
            if p and hasattr(p, 'create_completion'):
                available.append(name)
        except:
            pass
    return jsonify({"providers": sorted(available)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
