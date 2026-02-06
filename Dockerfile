FROM python:3.10-slim

# 安装依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc curl && \
    rm -rf /var/lib/apt/lists/*

# 安装 Python 包
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    'g4f[all]' \
    flask \
    flask-cors \
    gunicorn \
    requests \
    curl_cffi

WORKDIR /app

# 创建必要目录
RUN mkdir -p /tmp/g4f /tmp/har_and_cookies && \
    chmod -R 777 /tmp

COPY app.py .

EXPOSE 8080

# 使用更长的超时时间
CMD ["gunicorn", "-b", "0.0.0.0:8080", "-w", "1", "--timeout", "180", "--log-level", "debug", "app:app"]
