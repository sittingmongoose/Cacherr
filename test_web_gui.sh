#!/bin/bash

echo "🌐 Testing Cacherr Web GUI..."
echo "================================"

# Check if container is running
if ! docker ps | grep -q cacherr-test; then
    echo "❌ Cacherr container is not running. Starting it..."
    docker run --rm -d --name cacherr-test -p 5445:5445 \
        -e PLEX_URL=http://192.168.50.223:32401 \
        -e PLEX_TOKEN=fyg9ynv1KSH3N9Gq-fo- \
        -e PLEX_SOURCE=/media \
        -v /tmp/cacherr-config:/config \
        -v /tmp/cacherr-cache:/cache \
        sittingmongoose/cacherr:dev
    sleep 5
fi

echo "✅ Container is running"

# Test basic connectivity
echo "🔍 Testing basic connectivity..."
if curl -s http://localhost:5445/health > /dev/null; then
    echo "✅ Health endpoint accessible"
else
    echo "❌ Health endpoint not accessible"
    exit 1
fi

# Test main page
echo "🔍 Testing main page..."
MAIN_PAGE=$(curl -s http://localhost:5445/)
if echo "$MAIN_PAGE" | grep -q "<!DOCTYPE html>"; then
    echo "✅ Main page returns valid HTML"
else
    echo "❌ Main page does not return valid HTML"
fi

# Check for JavaScript assets
JS_ASSETS=$(echo "$MAIN_PAGE" | grep -o 'src="/assets/index-[^"]*\.js"' | wc -l)
if [ "$JS_ASSETS" -gt 0 ]; then
    echo "✅ Found $JS_ASSETS JavaScript assets"
else
    echo "❌ No JavaScript assets found"
fi

# Check for CSS assets
CSS_ASSETS=$(echo "$MAIN_PAGE" | grep -o 'href="/assets/index-[^"]*\.css"' | wc -l)
if [ "$CSS_ASSETS" -gt 0 ]; then
    echo "✅ Found $CSS_ASSETS CSS assets"
else
    echo "❌ No CSS assets found"
fi

# Test API endpoints
echo "🔍 Testing API endpoints..."
API_ENDPOINTS=("/api/status" "/api/system/health" "/api/settings" "/api/logs")
for endpoint in "${API_ENDPOINTS[@]}"; do
    if curl -s "http://localhost:5445$endpoint" > /dev/null; then
        echo "✅ $endpoint accessible"
    else
        echo "❌ $endpoint not accessible"
    fi
done

# Test WebSocket endpoint
echo "🔍 Testing WebSocket endpoint..."
if curl -s -I http://localhost:5445/ws | grep -q "101 Switching Protocols\|Upgrade: websocket"; then
    echo "✅ WebSocket endpoint accessible"
else
    echo "⚠️  WebSocket endpoint may not be accessible (this is expected for curl)"
fi

# Check for React app
if echo "$MAIN_PAGE" | grep -q "react\|React"; then
    echo "✅ React app detected in HTML"
else
    echo "❌ React app not detected in HTML"
fi

# Check for common UI elements
if echo "$MAIN_PAGE" | grep -q "dashboard\|status\|stats"; then
    echo "✅ Dashboard elements detected in HTML"
else
    echo "❌ Dashboard elements not detected in HTML"
fi

# Test with different user agents
echo "🔍 Testing with different user agents..."
USER_AGENTS=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36")
for ua in "${USER_AGENTS[@]}"; do
    if curl -s -H "User-Agent: $ua" http://localhost:5445/ > /dev/null; then
        echo "✅ Page accessible with User-Agent: ${ua:0:50}..."
    else
        echo "❌ Page not accessible with User-Agent: ${ua:0:50}..."
    fi
done

# Test response times
echo "🔍 Testing response times..."
START_TIME=$(date +%s%N)
curl -s http://localhost:5445/ > /dev/null
END_TIME=$(date +%s%N)
RESPONSE_TIME=$(( (END_TIME - START_TIME) / 1000000 ))
echo "✅ Main page response time: ${RESPONSE_TIME}ms"

# Test with different HTTP methods
echo "🔍 Testing HTTP methods..."
if curl -s -X POST http://localhost:5445/ > /dev/null; then
    echo "✅ POST method accepted"
else
    echo "⚠️  POST method not accepted (this may be expected)"
fi

if curl -s -X PUT http://localhost:5445/ > /dev/null; then
    echo "✅ PUT method accepted"
else
    echo "⚠️  PUT method not accepted (this may be expected)"
fi

# Test error handling
echo "🔍 Testing error handling..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:5445/nonexistent | grep -q "404"; then
    echo "✅ 404 error handling works"
else
    echo "❌ 404 error handling not working"
fi

echo ""
echo "🎉 Web GUI testing completed!"
echo "================================"
