FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装最新版 g4f
RUN pip install --no-cache-dir --upgrade \
    pip \
    g4f \
    flask \
    flask-cors \
    gunicorn

WORKDIR /app

RUN mkdir -p /tmp/g4f /tmp/har_and_cookies && \
    chmod -R 777 /tmp

COPY app.py .

EXPOSE 8080
CMD ["gunicorn", "-b", "0.0.0.0:8080", "-w", "1", "--timeout", "300", "app:app"]
