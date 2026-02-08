FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

RUN pip install --no-cache-dir flask g4f curl_cffi

WORKDIR /app
COPY app.py .

RUN mkdir -p /app/har_and_cookies && chmod 777 /app/har_and_cookies

EXPOSE 8080
CMD ["python", "app.py"]
