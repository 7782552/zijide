FROM python:3.10-slim

RUN pip install --no-cache-dir g4f flask flask-cors gunicorn

WORKDIR /app
COPY app.py .

RUN mkdir -p /tmp/g4f && chmod 777 /tmp/g4f

EXPOSE 8080
CMD ["gunicorn", "-b", "0.0.0.0:8080", "-w", "1", "--timeout", "60", "app:app"]
