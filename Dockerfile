FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*
RUN mkdir -p /var/log/gunicorn
RUN chmod 777 /var/log/gunicorn
RUN mkdir -p /etc/cron.d
RUN chmod 777 /etc/cron.d
RUN apt-get update && apt-get install -y cron
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY Django/ .