FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=UTC

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    bash \
    ca-certificates \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY main.py .
COPY dashboard.html .

# Create necessary directories
RUN mkdir -p /app/logs /app/cache /app/data

# Set proper permissions
RUN chmod -R 755 /app

# Expose default web port
EXPOSE 5443

# Run as root (simpler for Unraid)
USER root

# Simple command without complex entrypoint
CMD ["python", "main.py"]
