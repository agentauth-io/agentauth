FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY README.md .
COPY app/ app/
COPY alembic/ alembic/
COPY alembic.ini .
COPY server.py .
COPY demo.html .

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Railway sets PORT dynamically, server.py reads it from env
CMD ["python", "server.py"]

