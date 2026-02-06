FROM python:3.10-slim

RUN pip install flask flask-cors gunicorn requests

WORKDIR /app
COPY app.py .

EXPOSE 8080
CMD ["gunicorn", "-b", "0.0.0.0:8080", "-w", "1", "--timeout", "60", "app:app"]
