#!/bin/bash

# Production debugging script for Cacherr
# Use this when you need to debug the production build

set -e

echo "🔧 Cacherr Production Debugging"
echo "==============================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if production container is running
if ! docker ps | grep -q "cacherr-unraid"; then
    echo "❌ Production container is not running."
    echo "Please start it with: docker-compose up -d"
    exit 1
fi

echo "✅ Production container is running"
echo ""

# Show container status
echo "📊 Container Status:"
docker-compose ps

echo ""
echo "🔍 Debugging Production Build:"
echo "1. Open http://localhost:5445 in Chrome"
echo "2. Press F12 to open Chrome DevTools"
echo "3. Check Console tab for JavaScript errors"
echo "4. Check Network tab for API issues"
echo "5. Check Application tab for storage problems"
echo ""

# Show recent logs
echo "📝 Recent Logs (last 50 lines):"
docker-compose logs --tail=50 cacherr-unraid

echo ""
echo "🔧 Useful Commands:"
echo "View live logs: docker-compose logs -f cacherr-unraid"
echo "Check container resources: docker stats cacherr-unraid"
echo "Access container shell: docker exec -it cacherr-unraid /bin/bash"
echo "Restart container: docker-compose restart cacherr-unraid"
echo ""

# Check if DEBUG mode is enabled
if docker-compose exec cacherr-unraid printenv | grep -q "DEBUG=true"; then
    echo "✅ DEBUG mode is enabled"
else
    echo "⚠️  DEBUG mode is disabled"
    echo "To enable debugging, add to your .env file:"
    echo "DEBUG=true"
    echo "LOG_LEVEL=DEBUG"
    echo "Then restart the container: docker-compose restart cacherr-unraid"
fi

echo ""
echo "💡 Tip: For better debugging, use the development mode:"
echo "./dev-start.sh"
