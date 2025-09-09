# Minimal production Dockerfile for Cacherr (linux/amd64)
FROM --platform=linux/amd64 python:3.11-slim

LABEL maintainer="Cacherr" \
      description="Cacherr - Plex media caching with WebGUI" \
      org.opencontainers.image.source="https://github.com/sittingmongoose/cacherr"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    TZ=UTC \
    PATH="/app:$PATH" \
    PYTHONPATH="/app/src"

RUN apt-get update && apt-get install -y --no-install-recommends \
      curl ca-certificates tzdata gosu \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Non-root user
RUN groupadd -r cacherr && useradd -r -g cacherr cacherr

WORKDIR /app

# Dependencies first (better caching)
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy prebuilt frontend assets if present
COPY frontend/dist ./frontend/dist

# Copy application source
COPY src/ ./src/
COPY main.py .
COPY entrypoint.sh .

# Prepare runtime
RUN mkdir -p /config /cache /logs && \
    chown -R cacherr:cacherr /app && \
    chmod +x /app/entrypoint.sh

EXPOSE 5445

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -fsS http://localhost:5445/health || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "main.py"]

