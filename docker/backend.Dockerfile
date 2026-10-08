# Multi-stage: build the React app (stage 1), then bake it into the backend image
# (stage 2). FastAPI serves BOTH the SPA and /api on one port, so there is NO
# separate nginx container. Build context is the REPO ROOT (see docker-compose.yml)
# so this file can reach both ./frontend and ./backend.

# ---------- Stage 1: build the React frontend ----------
FROM node:20-alpine AS frontend-build
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# ---------- Stage 2: backend (Playwright + FastAPI + baked frontend) ----------
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

# System deps for postgres & build tools
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

# Bake the built React app where FastAPI serves it from (see api/main.py).
COPY --from=frontend-build /web/dist ./static_dist

# Run migrations then start the API. No --reload: this is a production image.
# (A local dev override can add --reload and a source mount; the shipped image must not.)
EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn api.main:app --host 0.0.0.0 --port 8000"]
