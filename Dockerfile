FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=UTC \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    bash \
    ca-certificates \
    tzdata \
    procps \
    gosu \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd -r plexcache && useradd -r -g plexcache plexcache

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY main.py .
COPY dashboard.html .
COPY entrypoint.sh .

# Create necessary directories with proper ownership
RUN mkdir -p /config/logs /config/data /cache && \
    chown -R plexcache:plexcache /app && \
    chown -R plexcache:plexcache /config && \
    chown -R plexcache:plexcache /cache

# Set proper permissions
RUN chmod -R 755 /app && \
    chmod -R 755 /config && \
    chmod -R 755 /cache && \
    chmod +x entrypoint.sh

# Keep as root for entrypoint script to work properly
# USER plexcache

# Expose default web port
EXPOSE 5443

# Health check (run as plexcache user)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5443/health || exit 1

# Default command
ENTRYPOINT ["./entrypoint.sh"]
CMD ["python", "main.py"]
