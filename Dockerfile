FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

# Копируем папку Django в контейнер
COPY Django/ .

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]