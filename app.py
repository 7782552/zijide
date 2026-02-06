import requests
import json
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def chat_ddg(message):
    """用 DuckDuckGo AI"""
    try:
        # 第一步：获取 token
        status_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "*/*",
            "x-vqd-accept": "1"
        }
        status_resp = requests.get(
            "https://duckduckgo.com/duckchat/v1/status", 
            headers=status_headers,
            timeout=10
        )
        token = status_resp.headers.get("x-vqd-4", "")
        
        if not token:
            raise Exception("No token")
        
        # 第二步：发送聊天请求
        chat_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/event-stream",
            "Content-Type": "application/json",
            "x-vqd-4": token
        }
        
        chat_data = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": message}]
        }
        
        chat_resp = requests.post(
            "https://duckduckgo.com/duckchat/v1/chat",
            headers=chat_headers,
            json=chat_data,
            timeout=30
        )
        
        # 第三步：解析 SSE 响应
        result = ""
        for line in chat_resp.text.split("\n"):
            line = line.strip()
            if not line:
                continue
            if line.startswith("data: "):
                data_str = line[6:]
                if data_str == "[DONE]":
                    break
                try:
                    data_json = json.loads(data_str)
                    if "message" in data_json:
                        result += data_json["message"]
                except:
                    continue
        
        if not result:
            raise Exception("Empty response")
            
        return result
        
    except Exception as e:
        raise Exception(f"DDG error: {str(e)}")

@app.route("/")
def index():
    return """
    <h1>🚀 AI API</h1>
    <p><a href="/test">Test</a></p>
    """

@app.route("/test")
def test():
    try:
        msg = chat_ddg("用中文说你好")
        return jsonify({"status": "ok", "response": msg})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})

@app.route("/v1/chat/completions", methods=["POST"])
def chat():
    try:
        data = request.json or {}
        messages = data.get("messages", [])
        
        # 合并所有消息
        full_message = ""
        for m in messages:
            role = m.get("role", "")
            content = m.get("content", "")
            if role == "system":
                full_message += f"System: {content}\n"
            elif role == "user":
                full_message += f"{content}\n"
        
        full_message = full_message.strip()
        
        if not full_message:
            return jsonify({"error": "No message"}), 400
        
        content = chat_ddg(full_message)
        
        return jsonify({
            "id": "chatcmpl-ddg",
            "object": "chat.completion",
            "model": "gpt-4o-mini",
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

@app.route("/health")
def health():
    return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
