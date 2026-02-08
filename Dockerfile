FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装最新版 g4f
RUN pip install --no-cache-dir --upgrade \
    g4f[all] \
    flask \
    flask-cors \
    curl_cffi

WORKDIR /app

COPY app.py .

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

EXPOSE 7860
CMD ["python", "app.py"]
