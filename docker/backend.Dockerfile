FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

# System deps for postgres & build tools
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run migrations then start the API. No --reload: this is a production image.
# (A local dev override can add --reload and a source mount; the shipped image must not.)
EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn api.main:app --host 0.0.0.0 --port 8000"]