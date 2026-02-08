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

# 记录
found_gpt5 = []

@app.route("/")
def index():
    return """
    <h1>GPT-5 Hunter</h1>
    <ul>
        <li><a href="/find-gpt5">🎯 找出 GPT-5 的 Provider</a></li>
        <li><a href="/gpt5-result">📊 查看结果</a></li>
        <li><a href="/gpt5-code">💻 生成代码</a></li>
    </ul>
    """

@app.route("/health")
def health():
    return "OK"

@app.route("/find-gpt5")
def find_gpt5():
    """测试每个 Provider 找 GPT-5"""
    global found_gpt5
    found_gpt5 = []
    results = []
    
    all_providers = [p for p in dir(g4f.Provider) if not p.startswith('_') and p[0].isupper()]
    
    for name in all_providers:
        print(f"Testing: {name}")
        try:
            provider = getattr(g4f.Provider, name, None)
            if not provider:
                continue
            
            response = g4f.ChatCompletion.create(
                model="gpt-4",
                provider=provider,
                messages=[{"role": "user", "content": "What model are you? Reply in JSON."}],
                stream=False,
                timeout=30
            )
            
            resp_str = str(response)
            has_gpt5 = "gpt-5" in resp_str.lower()
            
            result = {
                "provider": name,
                "gpt5": "🎯 YES" if has_gpt5 else "no",
                "response": resp_str[:200]
            }
            results.append(result)
            
            if has_gpt5:
                found_gpt5.append({"provider": name, "response": resp_str[:500]})
                print(f"🎯 FOUND: {name}")
                
        except Exception as e:
            results.append({"provider": name, "gpt5": "error", "error": str(e)[:50]})
    
    return jsonify({
        "total": len(all_providers),
        "gpt5_count": len(found_gpt5),
        "gpt5_providers": found_gpt5,
        "all": results
    })

@app.route("/gpt5-result")
def gpt5_result():
    return jsonify({"gpt5_providers": found_gpt5})

@app.route("/gpt5-code")
def gpt5_code():
    if not found_gpt5:
        return jsonify({"message": "先访问 /find-gpt5"})
    
    p = found_gpt5[0]["provider"]
    
    code = f'''# GPT-5 专用代码
import g4f
from g4f.Provider import {p}

response = g4f.ChatCompletion.create(
    model="gpt-4",
    provider={p},
    messages=[{{"role": "user", "content": "你好"}}],
    stream=False
)
print(response)
'''
    return jsonify({"provider": p, "code": code})

@app.route("/v1/chat/completions", methods=["POST"])
def chat():
    data = request.json
    messages = data.get("messages")
    
    # 如果找到了 GPT-5，用它
    if found_gpt5:
        p = getattr(g4f.Provider, found_gpt5[0]["provider"], None)
        if p:
            response = g4f.ChatCompletion.create(
                model="gpt-4",
                provider=p,
                messages=messages,
                stream=False
            )
            return jsonify({
                "choices": [{"message": {"role": "assistant", "content": str(response)}}],
                "model": "gpt-5",
                "provider": found_gpt5[0]["provider"]
            })
    
    # 自动选择
    response = g4f.ChatCompletion.create(
        model="gpt-4",
        messages=messages,
        stream=False
    )
    return jsonify({
        "choices": [{"message": {"role": "assistant", "content": str(response)}}],
        "model": "gpt-4-auto"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
