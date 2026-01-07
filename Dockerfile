FROM python:3.11-slim

# Set labels for Unraid
LABEL maintainer="Cacherr"
LABEL org.opencontainers.image.title="Cacherr"
LABEL org.opencontainers.image.description="Intelligent Plex Media Caching for Unraid"

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create app directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories
RUN mkdir -p /config/logs /cache

# Expose port
EXPOSE 5445

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:5445/api/health || exit 1

# Run application
CMD ["python", "main.py", "--port", "5445"]
