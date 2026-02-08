FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade \
    g4f[all] \
    flask \
    flask-cors \
    curl_cffi

WORKDIR /app

COPY app.py .

EXPOSE 8080
CMD ["python", "app.py"]
