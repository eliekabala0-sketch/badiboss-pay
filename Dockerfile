FROM node:20-bookworm-slim AS frontend-build

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build && test -f dist/index.html

FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .
COPY main.py .
COPY scripts ./scripts

COPY --from=frontend-build /app/frontend/dist ./frontend/dist

RUN test -f frontend/dist/index.html && ls -la frontend/dist && ls -la frontend/dist/assets

CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
