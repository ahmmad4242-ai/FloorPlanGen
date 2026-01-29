FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for shapely and ortools
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Render.com sets PORT env variable automatically
ENV PORT=10000

# Run with uvicorn
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
