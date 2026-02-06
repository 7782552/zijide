FROM python:3.10-slim

RUN apt-get update && apt-get install -y gcc python3-dev && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir g4f flask flask-cors

WORKDIR /app
COPY app.py .

# Zeabur 会自动设置 PORT 环境变量
CMD ["python", "app.py"]
