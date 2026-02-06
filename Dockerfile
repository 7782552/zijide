FROM python:3.10-slim

RUN apt-get update && apt-get install -y gcc python3-dev && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir g4f flask flask-cors

WORKDIR /app
COPY app.py .

EXPOSE 7860

# 直接用 Flask 启动，不用 gunicorn
CMD ["python", "app.py"]
