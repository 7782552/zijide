FROM python:3.10-slim

RUN apt-get update && apt-get install -y gcc python3-dev && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir --upgrade g4f flask flask-cors gunicorn

WORKDIR /app

COPY app.py .

EXPOSE 8080
CMD ["gunicorn", "-b", "0.0.0.0:8080", "-w", "2", "--timeout", "120", "app:app"]
