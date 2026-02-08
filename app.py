import os
import g4f
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime

os.environ["G4F_DIR"] = "/tmp/g4f"
if not os.path.exists("/tmp/g4f"):
    os.makedirs("/tmp/g4f", mode=0o777)

app = Flask(__name__)
CORS(app)

# 记录成功的模型
success_log = []
# 测试结果
test_results = {}

def log_success(provider, model, response_preview):
    """记录成功的调用"""
    record = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "provider": provider,
        "model": model,
        "response_preview": str(response_preview)[:100]
    }
    success_log.append(record)
    if len(success_log) > 100:
        success_log.pop(0)
    print(f"✅ SUCCESS: Provider={provider}, Model={model}")

# 所有要测试的 Provider 和 Model 组合
TEST_CONFIGS = [
    # DuckDuckGo 系列
    {"provider": "DuckDuckGo", "model": "gpt-4o-mini"},
    {"provider": "DuckDuckGo", "model": "gpt-4o"},
    {"provider": "DuckDuckGo", "model": "claude-3-haiku"},
    {"provider": "DuckDuckGo", "model": "llama-3.1-70b"},
    {"provider": "DuckDuckGo", "model": "mixtral-8x7b"},
    
    # PollinationsAI 系列
    {"provider": "PollinationsAI", "model": "gpt-4o"},
    {"provider": "PollinationsAI", "model": "gpt-4o-mini"},
    {"provider": "PollinationsAI", "model": "claude-3.5-sonnet"},
    {"provider": "PollinationsAI", "model": "deepseek-chat"},
    {"provider": "PollinationsAI", "model": "deepseek-r1"},
    
    # 其他 Provider
    {"provider": "Blackbox", "model": "gpt-4o"},
    {"provider": "Blackbox", "model": "claude-3.5-sonnet"},
    {"provider": "Blackbox", "model": "deepseek-chat"},
    {"provider": "DeepInfra", "model": "llama-3.1-70b"},
    {"provider": "DeepInfra", "model": "mixtral-8x7b"},
    {"provider": "Phind", "model": "gpt-4o"},
    {"provider": "You", "model": "gpt-4o"},
    {"provider": "ChatGptEs", "model": "gpt-4o"},
    {"provider": "FreeGpt", "model": "gpt-4o"},
]

def test_single_model(provider_name, model_name, test_message="Say OK"):
    """测试单个模型"""
    try:
        provider = getattr(g4f.Provider, provider_name, None)
        if not provider:
            return {"status": "❌", "error": f"Provider {provider_name} not found"}
        
        start_time = datetime.now()
        response = g4f.ChatCompletion.create(
            model=model_name,
            provider=provider,
            messages=[{"role": "user", "content": test_message}],
            stream=False,
            timeout=30
        )
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        response_str = str(response)
        
        # 检查是否真的成功
        if not response:
            return {"status": "❌", "error": "Empty response"}
        if "error" in response_str.lower():
            return {"status": "❌", "error": response_str[:100]}
        if "upgrade" in response_str.lower():
            return {"status": "❌", "error": "Requires upgrade"}
        if "rate limit" in response_str.lower():
            return {"status": "⚠️", "error": "Rate limited"}
        
        return {
            "status": "✅",
            "duration": f"{duration:.2f}s",
            "response": response_str[:100]
        }
        
    except Exception as e:
        return {"status": "❌", "error": str(e)[:100]}

@app.route("/")
def index():
    html = """
    <h1>G4F Top Models API</h1>
    <p>Status: Running</p>
    <ul>
        <li><a href="/test-all">🧪 测试所有模型</a> (需要几分钟)</li>
        <li><a href="/test-results">📊 查看测试结果</a></li>
        <li><a href="/working-models">✅ 只看能用的模型</a></li>
        <li><a href="/logs">📝 查看调用日志</a></li>
        <li><a href="/generate-code">💻 生成最佳模型代码</a></li>
    </ul>
    """
    return html

@app.route("/health")
def health():
    return "OK"

@app.route("/logs")
def logs():
    return jsonify({"total": len(success_log), "logs": success_log[-20:]})

@app.route("/v1/models", methods=["GET"])
def models():
    return jsonify({"models": ["gpt-4o", "gpt-4o-mini", "claude-3-haiku", "llama-3.1-70b", "mixtral-8x7b"]})

@app.route("/test-all")
def test_all():
    """测试所有模型"""
    global test_results
    test_results = {
        "test_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "results": []
    }
    
    for config in TEST_CONFIGS:
        provider = config["provider"]
        model = config["model"]
        print(f"🔄 Testing: {provider} + {model}")
        
        result = test_single_model(provider, model)
        result["provider"] = provider
        result["model"] = model
        test_results["results"].append(result)
    
    # 统计
    total = len(test_results["results"])
    success = len([r for r in test_results["results"] if r["status"] == "✅"])
    
    test_results["summary"] = {
        "total": total,
        "success": success,
        "failed": total - success,
        "success_rate": f"{success/total*100:.1f}%"
    }
    
    return jsonify(test_results)

@app.route("/test-results")
def get_test_results():
    """获取测试结果"""
    if not test_results:
        return jsonify({"message": "还没有测试结果，请先访问 /test-all"})
    return jsonify(test_results)

@app.route("/working-models")
def working_models():
    """只显示能用的模型"""
    if not test_results:
        return jsonify({"message": "还没有测试结果，请先访问 /test-all"})
    
    working = [r for r in test_results["results"] if r["status"] == "✅"]
    return jsonify({
        "test_time": test_results.get("test_time"),
        "count": len(working),
        "working_models": working
    })

@app.route("/generate-code")
def generate_code():
    """生成最佳模型的单独代码"""
    if not test_results:
        return jsonify({"message": "还没有测试结果，请先访问 /test-all"})
    
    working = [r for r in test_results["results"] if r["status"] == "✅"]
    
    if not working:
        return jsonify({"message": "没有找到能用的模型"})
    
    # 按速度排序，取最快的
    best = sorted(working, key=lambda x: float(x.get("duration", "999s").replace("s", "")))[0]
    
    code = f'''# 🎯 最佳模型代码
# Provider: {best["provider"]}
# Model: {best["model"]}
# 速度: {best.get("duration", "N/A")}
# 测试时间: {test_results.get("test_time")}

import g4f
from g4f.Provider import {best["provider"]}

def chat(message):
    response = g4f.ChatCompletion.create(
        model="{best["model"]}",
        provider={best["provider"]},
        messages=[{{"role": "user", "content": message}}],
        stream=False
    )
    return response

# 使用示例
result = chat("你好")
print(result)
'''
    
    # 生成所有能用模型的代码
    all_working_code = "# 所有能用的模型配置\\n\\nWORKING_MODELS = [\\n"
    for w in working:
        all_working_code += f'    {{"provider": "{w["provider"]}", "model": "{w["model"]}", "duration": "{w.get("duration", "N/A")}"}},\\n'
    all_working_code += "]"
    
    return jsonify({
        "best_model": best,
        "best_model_code": code,
        "all_working_models": working,
        "all_working_code": all_working_code
    })

@app.route("/v1/chat/completions", methods=["POST"])
def chat():
    data = request.json
    messages = data.get("messages")
    model = data.get("model", "gpt-4o")
    
    # 如果有测试结果，优先用能用的模型
    if test_results and test_results.get("results"):
        working = [r for r in test_results["results"] if r["status"] == "✅"]
        for w in working:
            try:
                provider = getattr(g4f.Provider, w["provider"], None)
                if provider:
                    response = g4f.ChatCompletion.create(
                        model=w["model"],
                        provider=provider,
                        messages=messages,
                        stream=False
                    )
                    if response and "error" not in str(response).lower() and "upgrade" not in str(response).lower():
                        log_success(w["provider"], w["model"], response)
                        return jsonify({
                            "choices": [{"message": {"role": "assistant", "content": str(response)}}],
                            "model": w["model"],
                            "provider": w["provider"]
                        })
            except:
                continue
    
    # 默认尝试
    providers_to_try = [
        ("DuckDuckGo", "gpt-4o-mini"),
        ("DuckDuckGo", "claude-3-haiku"),
        ("PollinationsAI", "gpt-4o"),
    ]
    
    for provider_name, model_name in providers_to_try:
        try:
            provider = getattr(g4f.Provider, provider_name, None)
            if provider:
                response = g4f.ChatCompletion.create(
                    model=model_name,
                    provider=provider,
                    messages=messages,
                    stream=False
                )
                if response and "error" not in str(response).lower() and "upgrade" not in str(response).lower():
                    log_success(provider_name, model_name, response)
                    return jsonify({
                        "choices": [{"message": {"role": "assistant", "content": str(response)}}],
                        "model": model_name,
                        "provider": provider_name
                    })
        except:
            continue
    
    return jsonify({"error": "所有模型失败"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
