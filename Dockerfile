FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    curl \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade \
    g4f[all] \
    flask \
    flask-cors \
    gunicorn \
    curl_cffi

WORKDIR /app

# 创建所有必要目录
RUN mkdir -p /tmp/g4f /tmp/har_and_cookies /app/har_and_cookies && \
    chmod -R 777 /tmp /app

COPY app.py .

EXPOSE 8080
CMD ["gunicorn", "-b", "0.0.0.0:8080", "-w", "1", "--timeout", "300", "app:app"]
