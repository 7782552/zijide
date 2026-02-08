FROM python:3.10-alpine

RUN pip install --no-cache-dir flask g4f

WORKDIR /app
COPY app.py .

EXPOSE 8080
CMD ["python", "app.py"]
