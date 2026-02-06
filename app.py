import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def chat_ddg(message):
    """用 DuckDuckGo AI"""
    # 获取 token
    headers = {"x-vqd-accept": "1"}
    r = requests.get("https://duckduckgo.com/duckchat/v1/status", headers=headers)
    token = r.headers.get("x-vqd-4", "")
    
    # 发送消息
    headers = {"x-vqd-4": token, "Content-Type": "application/json"}
    data = {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": message}]}
    r = requests.post("https://duckduckgo.com/duckchat/v1/chat", headers=headers, json=data)
    
    # 解析响应
    result = ""
    for line in r.text.split("\n"):
        if line.startswith("data: ") and "[DONE]" not in line:
            try:
                import json
                j = json.loads(line[6:])
                result += j.get("message", "")
            except:
                pass
    return result

@app.route("/")
def index():
    return "<h1>API OK</h1><a href='/test'>Test</a>"

@app.route("/test")
def test():
    try:
        msg = chat_ddg("说你好")
        return jsonify({"status": "ok", "response": msg})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})

@app.route("/v1/chat/completions", methods=["POST"])
def chat():
    try:
        data = request.json or {}
        messages = data.get("messages", [])
        
        # 提取用户消息
        user_msg = ""
        for m in messages:
            if m.get("role") == "user":
                user_msg = m.get("content", "")
        
        content = chat_ddg(user_msg)
        
        return jsonify({
            "choices": [{
                "message": {"role": "assistant", "content": content}
            }]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
