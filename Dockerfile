FROM python:3.10-slim

# 安装依赖
RUN apt-get update && apt-get install -y gcc python3-dev curl && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir --upgrade g4f flask flask-cors gunicorn

# 设置工作目录
WORKDIR /app

# 复制应用代码
COPY app.py .

EXPOSE 7860

# 使用 gunicorn 生产环境部署
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "--workers", "2", "--timeout", "120", "app:app"]
