# ===========================================
# Production Dockerfile for Cacherr
# Multi-stage build: Frontend → Backend (single image)
# ===========================================

# ---------- Frontend build stage ----------
FROM node:20-bullseye-slim AS frontend-build
WORKDIR /frontend

# Install deps
COPY frontend/package*.json ./
RUN npm ci

# Build assets
COPY frontend/ ./
RUN npm run build

# ---------- Backend runtime stage ----------
FROM python:3.11-slim AS production

# Labels for container metadata
LABEL maintainer="Cacherr Team" \
      description="Docker-optimized Plex media caching system (single-image build)" \
      version="1.0.0"

# Set environment variables for production
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=UTC \
    DEBIAN_FRONTEND=noninteractive \
    PATH="/app:$PATH" \
    PYTHONPATH="/app/src"

# Install system dependencies (minimal for production)
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    tzdata \
    gosu \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r cacherr && useradd -r -g cacherr cacherr

# Set working directory
WORKDIR /app

# Copy and install Python dependencies first (for better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY src/ ./src/
COPY main.py .
COPY entrypoint.sh .

# Copy built frontend from build stage
COPY --from=frontend-build /frontend/dist ./frontend/dist

# Create necessary directories with proper permissions
RUN mkdir -p /config /logs /cache && \
    chown -R cacherr:cacherr /app /config /logs /cache && \
    chmod +x /app/entrypoint.sh

# Expose port
EXPOSE 5445

# Health check for production monitoring
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5445/health || exit 1

# Use entrypoint script for proper startup and permission handling
# Note: Entrypoint runs as root initially, then switches to cacherr user
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command for production (runs web server)
CMD ["python", "main.py"]
