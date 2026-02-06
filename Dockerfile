FROM python:3.10-slim

RUN pip install --no-cache-dir --upgrade pip g4f flask flask-cors gunicorn

WORKDIR /app

RUN mkdir -p /tmp/g4f && chmod 777 /tmp/g4f

COPY app.py .

EXPOSE 8080
CMD ["gunicorn", "-b", "0.0.0.0:8080", "-w", "1", "--timeout", "120", "app:app"]
