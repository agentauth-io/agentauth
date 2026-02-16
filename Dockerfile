FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY requirements.txt .
COPY README.md .
COPY app/ app/
COPY core/ core/
COPY agentauth_core/ agentauth_core/
COPY alembic/ alembic/
COPY alembic.ini .
COPY production_server.py .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port (Railway/Render/Fly set PORT dynamically)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Start command - uses PORT env var from platform
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --reload"]

