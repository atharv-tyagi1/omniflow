FROM python:3.12-slim

# Create a non-root user and group
RUN groupadd -r omniflow && useradd -r -g omniflow omniflow

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000

WORKDIR /app

# Install system dependencies securely
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app/backend/

# Change ownership to the non-root user
RUN chown -R omniflow:omniflow /app

# Switch to non-root user
USER omniflow

EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the application using canonical import path
CMD ["sh", "-c", "cd /app/backend && alembic upgrade head && cd /app && uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT}"]
