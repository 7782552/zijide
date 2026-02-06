import os
import sys

# 环境设置
os.environ["G4F_DIR"] = "/tmp/g4f"
os.makedirs("/tmp/g4f", exist_ok=True)

from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def get_response(messages):
    """获取 AI 响应"""
    import g4f
    
    # 打印调试信息
    print(f"g4f version: {g4f.version if hasattr(g4f, 'version') else 'unknown'}")
    
    errors = []
    
    # 方法1: 直接调用，让 g4f 自动选择
    try:
        response = g4f.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=messages
        )
        if response:
            return str(response), "auto"
    except Exception as e:
        errors.append(f"auto: {e}")
    
    # 方法2: 使用 Client API
    try:
        from g4f.client import Client
        client = Client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        if response and response.choices:
            return response.choices[0].message.content, "client"
    except Exception as e:
        errors.append(f"client: {e}")
    
    # 方法3: 遍历所有 provider
    try:
        from g4f.Provider import __all__ as providers
        import g4f.Provider as P
        
        for name in providers[:10]:
            try:
                provider = getattr(P, name, None)
                if not provider:
                    continue
                
                response = g4f.ChatCompletion.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    provider=provider
                )
                
                if response and len(str(response)) > 2:
                    return str(response), name
            except:
                continue
    except Exception as e:
        errors.append(f"providers: {e}")
    
    raise Exception(f"All methods failed: {errors}")

@app.route("/")
def index():
    # 检查 g4f 状态
    try:
        import g4f
        version = g4f.version if hasattr(g4f, 'version') else 'unknown'
        
        from g4f.Provider import __all__ as providers
        provider_count = len(providers)
        provider_list = ', '.join(providers[:20])
    except Exception as e:
        version = f"Error: {e}"
        provider_count = 0
        provider_list = "N/A"
    
    return f"""
    <html>
    <head><title>G4F API</title></head>
    <body>
        <h1>🚀 G4F API</h1>
        <p><b>G4F Version:</b> {version}</p>
        <p><b>Providers ({provider_count}):</b> {provider_list}...</p>
        <hr>
        <p><a href="/test">🧪 Test API</a></p>
        <p><a href="/debug">🔍 Debug Info</a></p>
    </body>
    </html>
    """

@app.route("/debug")
def debug():
    """调试信息"""
    info = {}
    
    try:
        import g4f
        info["g4f_imported"] = True
        info["g4f_version"] = g4f.version if hasattr(g4f, 'version') else 'unknown'
    except Exception as e:
        info["g4f_imported"] = False
        info["g4f_error"] = str(e)
    
    try:
        from g4f.Provider import __all__ as providers
        info["providers"] = providers
    except Exception as e:
        info["providers_error"] = str(e)
    
    try:
        from g4f.client import Client
        info["client_available"] = True
    except Exception as e:
        info["client_available"] = False
        info["client_error"] = str(e)
    
    return jsonify(info)

@app.route("/test")
def test():
    try:
        content, method = get_response([{"role": "user", "content": "Say hello"}])
        return jsonify({
            "status": "success",
            "method": method,
            "response": content[:500]
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route("/v1/chat/completions", methods=["POST"])
def chat():
    try:
        data = request.json or {}
        messages = data.get("messages", [])
        
        if not messages:
            return jsonify({"error": "messages required"}), 400
        
        content, method = get_response(messages)
        
        return jsonify({
            "id": "chatcmpl-g4f",
            "object": "chat.completion",
            "model": "gpt-4o-mini",
            "method": method,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content
                },
                "finish_reason": "stop"
            }]
        })
    except Exception as e:
        return jsonify({"error": {"message": str(e)}}), 500

@app.route("/health")
def health():
    return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
