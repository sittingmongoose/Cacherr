FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
WORKDIR /app

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY plexcache.py .
COPY plexcache_settings.json .
COPY plexcache_setup.py .

# Create necessary directories
RUN mkdir -p /mnt/user/system/plexcache /app/logs

# Set permissions
RUN chmod +x plexcache.py

# Expose port for web interface
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Default command - run in web server mode
CMD ["python3", "plexcache.py", "--web", "--host", "0.0.0.0", "--port", "5000"]