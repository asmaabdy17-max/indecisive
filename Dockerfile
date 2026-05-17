FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    playwright install

COPY . .

RUN mkdir -p logs data/output

ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["python", "main.py"]
