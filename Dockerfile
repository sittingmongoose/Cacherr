# Multi-stage build for production deployment
# Stage 1: Frontend Build
FROM node:20-alpine AS frontend-builder

# Set working directory for frontend
WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package.json ./

# Install frontend dependencies (including dev dependencies for build)
RUN npm install --silent

# Copy frontend source code
COPY frontend/ ./

# Build frontend for production
RUN npm run build

# Stage 2: Python Backend
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
RUN groupadd -r cacherr && useradd -r -g cacherr cacherr

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy built frontend assets from the frontend builder stage
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist/

# Copy application code
COPY src/ ./src/
COPY main.py .
COPY dashboard.html .
COPY entrypoint.sh .

# SECURITY: Create directories with minimal permissions - NO ownership changes
# Mount-aware permission handling is done safely in entrypoint.sh at runtime
RUN mkdir -p /config/logs /config/data /cache

# SECURITY CRITICAL: ONLY modify ownership/permissions on application code directory
# NEVER modify /config or /cache here as they are commonly mounted from host system
RUN chown -R cacherr:cacherr /app && \
    chmod -R 755 /app && \
    chmod +x /app/entrypoint.sh

# SECURITY NOTE: /config and /cache ownership handled by entrypoint.sh
# The entrypoint uses mount detection to avoid modifying host-mounted directories

# Keep as root for entrypoint script to work properly
# USER cacherr

# Expose default web port
EXPOSE 5445

# Health check (run as cacherr user)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5445/health || exit 1

# Default command
ENTRYPOINT ["/bin/bash", "./entrypoint.sh"]
CMD ["python", "main.py"]
