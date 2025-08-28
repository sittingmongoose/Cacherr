#!/bin/bash

# Development startup script for Cacherr
# This script starts the development environment with hot reloading

set -e

echo "🚀 Starting Cacherr Development Environment"
echo "=========================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating from env.example..."
    if [ -f "env.example" ]; then
        cp env.example .env
        echo "✅ Created .env from env.example"
        echo "⚠️  Please edit .env with your actual configuration values"
        echo "   Press Enter to continue or Ctrl+C to cancel..."
        read
    else
        echo "❌ No env.example file found. Please create a .env file first."
        exit 1
    fi
fi

# Stop any existing containers
echo "🛑 Stopping any existing containers..."
docker-compose -f docker-compose.dev.yml down 2>/dev/null || true

# Build and start development environment
echo "🔨 Building development image..."
docker-compose -f docker-compose.dev.yml build

echo "🚀 Starting development services..."
docker-compose -f docker-compose.dev.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service status
echo "📊 Service Status:"
docker-compose -f docker-compose.dev.yml ps

echo ""
echo "✅ Development environment is ready!"
echo ""
echo "🌐 Frontend (React Dev Server): http://localhost:3000"
echo "🔧 Backend API: http://localhost:5445"
echo "📚 API Documentation: http://localhost:5445/docs"
echo ""
echo "🔍 Debugging Instructions:"
echo "1. Open http://localhost:3000 in Chrome"
echo "2. Press F12 to open Chrome DevTools"
echo "3. Go to Console tab for JavaScript errors"
echo "4. Go to Network tab for API request/response debugging"
echo "5. Go to Sources tab for breakpoint debugging"
echo ""
echo "📝 Logs:"
echo "Frontend logs: docker-compose -f docker-compose.dev.yml logs -f cacherr-dev"
echo "Backend logs: docker-compose -f docker-compose.dev.yml logs -f cacherr-dev | grep -v 'npm'"
echo ""
echo "🛑 To stop: docker-compose -f docker-compose.dev.yml down"
echo "🔄 To restart: ./dev-start.sh"
