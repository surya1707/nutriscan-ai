FROM python:3.11.9-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create non-root user and change ownership
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 10000
