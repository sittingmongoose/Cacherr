#!/bin/bash

echo "=== PlexCacheUltra Unraid Startup ==="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp env.simple .env
    echo "Please edit .env file with your Plex server details and paths"
    echo "Then run this script again"
    exit 1
fi

# Create necessary directories
echo "Creating data and logs directories..."
mkdir -p data logs

# Set permissions
echo "Setting permissions..."
chmod -R 755 data logs

# Start the container
echo "Starting PlexCacheUltra container..."
docker-compose up -d

echo "=== Container started! ==="
echo "Check logs with: docker-compose logs -f"
echo "Access web interface at: http://your-server-ip:5443"
