FROM python:3.10-slim

RUN apt-get update && apt-get install -y gcc python3-dev && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir g4f==0.3.3.0 flask flask-cors

WORKDIR /app
COPY app.py .

EXPOSE 8080
CMD ["python", "app.py"]
