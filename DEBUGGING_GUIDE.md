# Cacherr Web GUI Debugging Guide

This guide explains how to debug JavaScript and network errors in the Cacherr web GUI using Chrome DevTools and other debugging tools.

## 🚀 Quick Start - Development Mode (Recommended for Debugging)

### 1. Start Development Environment

```bash
# Make sure you're in the project directory
cd /mnt/user/Cursor/Cacherr

# Start development environment
./dev-start.sh
```

This will:
- Start the React dev server on port 3000 with hot reloading
- Start the Python backend on port 5445
- Enable source maps and debugging capabilities

### 2. Access the Application

- **Frontend**: http://localhost:3000 (React dev server with hot reload)
- **Backend API**: http://localhost:5445
- **API Docs**: http://localhost:5445/docs

### 3. Open Chrome DevTools

1. Navigate to http://localhost:3000
2. Press `F12` or right-click → "Inspect"
3. Use the following tabs for debugging:

#### Console Tab - JavaScript Errors
- View JavaScript errors, warnings, and console.log outputs
- See runtime errors with full stack traces
- Use `console.log()`, `console.error()`, etc. for debugging

#### Network Tab - API Requests
- Monitor all HTTP requests to the backend
- See request/response headers, payloads, and timing
- Filter by XHR/Fetch requests to focus on API calls
- Check for failed requests (red entries)

#### Sources Tab - Breakpoint Debugging
- Set breakpoints in your React components
- Step through code execution
- Inspect variables and call stack
- Use the debugger statement in your code

#### Application Tab - Storage & State
- View localStorage, sessionStorage
- Check cookies and cache
- Monitor service workers

## 🔧 Production Mode Debugging

If you need to debug the production build:

### 1. Enable Source Maps in Production

Edit your `docker-compose.yml` to enable debugging:

```yaml
environment:
  - DEBUG=true
  - LOG_LEVEL=DEBUG
```

### 2. Access Production Build

- **Web GUI**: http://localhost:5445 (served by Flask backend)
- **API**: http://localhost:5445/api/*

### 3. Debug Production Issues

Even in production, you can:
- Use Console tab for JavaScript errors
- Monitor Network tab for API issues
- Check Application tab for storage problems

## 🐛 Common Debugging Scenarios

### JavaScript Errors

1. **Runtime Errors**: Check Console tab for red error messages
2. **Syntax Errors**: Usually caught during build, check terminal output
3. **Type Errors**: Common in TypeScript, check for type mismatches

### Network/API Issues

1. **Failed Requests**: Look for red entries in Network tab
2. **CORS Issues**: Check browser console for CORS errors
3. **Authentication**: Verify API tokens and headers
4. **Rate Limiting**: Check for 429 responses

### Performance Issues

1. **Slow Loading**: Use Network tab timing information
2. **Memory Leaks**: Monitor Memory tab in DevTools
3. **Large Bundles**: Check Sources tab for large files

## 🛠️ Advanced Debugging Techniques

### 1. React Developer Tools

Install the React Developer Tools Chrome extension for:
- Component tree inspection
- Props and state monitoring
- Performance profiling

### 2. Redux DevTools (if using Redux)

Monitor state changes and actions in real-time.

### 3. Custom Debugging

Add debugging code to your components:

```typescript
// In your React components
useEffect(() => {
  console.log('Component mounted with props:', props);
  console.log('Current state:', state);
}, [props, state]);

// Debug API calls
const fetchData = async () => {
  try {
    console.log('Fetching data from:', apiUrl);
    const response = await fetch(apiUrl);
    console.log('Response status:', response.status);
    const data = await response.json();
    console.log('Response data:', data);
  } catch (error) {
    console.error('API error:', error);
  }
};
```

### 4. Network Request Debugging

```typescript
// Intercept fetch requests for debugging
const originalFetch = window.fetch;
window.fetch = function(...args) {
  console.log('Fetch request:', args);
  return originalFetch.apply(this, args).then(response => {
    console.log('Fetch response:', response);
    return response;
  });
};
```

## 📊 Monitoring and Logging

### 1. Container Logs

```bash
# View all logs
docker-compose -f docker-compose.dev.yml logs -f cacherr-dev

# View only backend logs (filter out npm output)
docker-compose -f docker-compose.dev.yml logs -f cacherr-dev | grep -v 'npm'

# View only frontend logs
docker-compose -f docker-compose.dev.yml logs -f cacherr-dev | grep 'npm'
```

### 2. Browser Logs

- **Console**: JavaScript errors and logs
- **Network**: API request/response details
- **Performance**: Load times and bottlenecks

### 3. Application Logs

Check `/config/logs/` directory for backend application logs.

## 🔍 Troubleshooting Common Issues

### 1. Port Conflicts

If ports 3000 or 5445 are already in use:

```bash
# Check what's using the ports
sudo netstat -tulpn | grep :3000
sudo netstat -tulpn | grep :5445

# Kill conflicting processes or change ports in docker-compose.dev.yml
```

### 2. Hot Reload Not Working

- Check that frontend source is properly mounted
- Verify npm dev server is running
- Check browser console for errors

### 3. API Connection Issues

- Verify backend is running on port 5445
- Check CORS settings in backend
- Verify API endpoints are correct

### 4. Build Issues

```bash
# Clean and rebuild
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml build --no-cache
docker-compose -f docker-compose.dev.yml up
```

## 🎯 Best Practices

1. **Always use development mode** for active debugging
2. **Check console first** for JavaScript errors
3. **Monitor network tab** for API issues
4. **Use source maps** for readable debugging
5. **Add strategic console.logs** for complex flows
6. **Test in multiple browsers** for compatibility issues

## 🚨 Emergency Debugging

If the web GUI is completely broken:

1. Check container status: `docker-compose ps`
2. View container logs: `docker-compose logs cacherr-dev`
3. Check system resources: `docker stats`
4. Restart container: `docker-compose restart cacherr-dev`
5. Rebuild if necessary: `docker-compose build --no-cache`

## 📚 Additional Resources

- [Chrome DevTools Documentation](https://developers.google.com/web/tools/chrome-devtools)
- [React Debugging Guide](https://react.dev/learn/react-developer-tools)
- [Vite Debugging](https://vitejs.dev/guide/troubleshooting.html)
- [Docker Debugging](https://docs.docker.com/config/containers/logging/)

---

**Remember**: Development mode gives you the best debugging experience with hot reloading, source maps, and detailed error reporting. Use production mode only when you need to test the final build.
