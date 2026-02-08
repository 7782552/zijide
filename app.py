from flask import Flask, request, jsonify
import g4f

app = Flask(__name__)

# 顶级模型配置
MODELS = {
    "gpt-4o": "gpt-4o",
    "gpt-4o-mini": "gpt-4o-mini", 
    "gpt-4-turbo": "gpt-4-turbo",
    "claude-3.5-sonnet": "claude-3.5-sonnet",
    "claude-3-opus": "claude-3-opus",
    "deepseek-r1": "deepseek-r1",
    "deepseek-chat": "deepseek-chat",
    "gemini-pro": "gemini-pro",
    "llama-3.1-70b": "llama-3.1-70b",
}

@app.route("/")
def home():
    return "G4F API - Top Models"

@app.route("/health")
def health():
    return "OK"

@app.route("/v1/models", methods=["GET"])
def list_models():
    return jsonify({"models": list(MODELS.keys())})

@app.route("/providers", methods=["GET"])
def list_providers():
    providers = [p for p in dir(g4f.Provider) if not p.startswith('_')]
    return jsonify({"count": len(providers), "providers": providers})

@app.route("/v1/chat/completions", methods=["POST"])
def chat():
    try:
        data = request.json
        messages = data.get("messages", [])
        model = data.get("model", "gpt-4o-mini")
        
        # 尝试多个方式
        response = None
        error_msg = ""
        
        # 方法1: 自动选择 provider
        try:
            response = g4f.ChatCompletion.create(
                model=model,
                messages=messages
            )
        except Exception as e:
            error_msg = str(e)
        
        # 方法2: 用 Bing
        if not response:
            try:
                response = g4f.ChatCompletion.create(
                    model="gpt-4",
                    provider=g4f.Provider.Bing,
                    messages=messages
                )
            except:
                pass
        
        # 方法3: 用 You
        if not response:
            try:
                response = g4f.ChatCompletion.create(
                    model="gpt-4o-mini",
                    provider=g4f.Provider.You,
                    messages=messages
                )
            except:
                pass
        
        # 方法4: 用 Blackbox
        if not response:
            try:
                response = g4f.ChatCompletion.create(
                    model=model,
                    provider=g4f.Provider.Blackbox,
                    messages=messages
                )
            except:
                pass

        # 方法5: 用 DeepInfra
        if not response:
            try:
                response = g4f.ChatCompletion.create(
                    model="llama-3.1-70b",
                    provider=g4f.Provider.DeepInfra,
                    messages=messages
                )
            except:
                pass
        
        if response:
            return jsonify({
                "id": "chatcmpl-g4f",
                "model": model,
                "choices": [{
                    "index": 0,
                    "message": {"role": "assistant", "content": response},
                    "finish_reason": "stop"
                }]
            })
        else:
            return jsonify({"error": f"All providers failed: {error_msg}"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/test", methods=["GET"])
def test():
    """测试哪些模型能用"""
    results = {}
    test_msg = [{"role": "user", "content": "say OK"}]
    
    providers_to_test = ["Bing", "You", "Blackbox", "DeepInfra", "Gemini", "Phind"]
    
    for p_name in providers_to_test:
        try:
            provider = getattr(g4f.Provider, p_name, None)
            if provider:
                resp = g4f.ChatCompletion.create(
                    model="gpt-4o-mini",
                    provider=provider,
                    messages=test_msg,
                    timeout=15
                )
                results[p_name] = {"status": "✅", "response": str(resp)[:50]}
        except Exception as e:
            results[p_name] = {"status": "❌", "error": str(e)[:50]}
    
    return jsonify(results)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
