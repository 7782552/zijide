FROM python:3.10-slim

RUN apt-get update && apt-get install -y gcc python3-dev curl && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir --upgrade g4f flask flask-cors gunicorn

WORKDIR /app

# 创建必要的目录并设置权限
RUN mkdir -p /tmp/g4f /tmp/har_and_cookies && \
    chmod -R 777 /tmp/g4f /tmp/har_and_cookies

COPY app.py .

EXPOSE 8080
CMD ["gunicorn", "-b", "0.0.0.0:8080", "-w", "2", "--timeout", "120", "app:app"]
