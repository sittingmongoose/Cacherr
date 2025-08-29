#!/bin/bash

echo "🧪 Quick Logs Tab Test Runner"
echo "================================"

echo "📋 Checking prerequisites..."
if ! docker --version > /dev/null 2>&1; then
    echo "❌ Docker not available"
    exit 1
fi

if ! docker-compose --version > /dev/null 2>&1; then
    echo "❌ Docker Compose not available"
    exit 1
fi

echo "✅ Docker environment ready"

# Check if frontend is running
echo "🌐 Checking frontend availability..."
if curl -s -f http://192.168.50.223:3001/ > /dev/null; then
    echo "✅ Frontend is running on port 3001"
else
    echo "❌ Frontend not accessible on port 3001"
    echo "💡 Make sure to run: cd frontend && npm run dev -- --port 3001"
    exit 1
fi

echo "🚀 Running Playwright tests for logs tab..."
echo "-------------------------------------------"

# Run only our logs tab tests
docker-compose run --rm playwright npx playwright test logs-tab.spec.ts --project=chromium --reporter=list --timeout=60000

echo ""
echo "📊 Test execution completed!"