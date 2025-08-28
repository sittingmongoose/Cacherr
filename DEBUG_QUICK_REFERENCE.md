# 🚀 Cacherr Debugging Quick Reference

## 🎯 Quick Start Commands

```bash
# Development Mode (Best for debugging)
./dev-start.sh

# Production Debugging
./debug-production.sh

# Stop Development
docker-compose -f docker-compose.dev.yml down

# Stop Production
docker-compose down
```

## 🌐 Access URLs

| Mode | Frontend | Backend | Notes |
|------|----------|---------|-------|
| **Development** | http://localhost:3000 | http://localhost:5445 | Hot reload, source maps |
| **Production** | http://localhost:5445 | http://localhost:5445 | Built frontend served by Flask |

## 🔍 Chrome DevTools Shortcuts

| Action | Shortcut |
|--------|----------|
| Open DevTools | `F12` or `Ctrl+Shift+I` |
| Console Tab | `Ctrl+Shift+J` |
| Network Tab | `Ctrl+Shift+E` |
| Sources Tab | `Ctrl+Shift+F8` |
| Application Tab | `Ctrl+Shift+F5` |

## 🐛 Common Issues & Solutions

### JavaScript Errors
- **Check**: Console tab (red errors)
- **Fix**: Look for syntax, type, or runtime errors
- **Debug**: Add `console.log()` statements

### Network/API Issues
- **Check**: Network tab (red failed requests)
- **Fix**: Verify API endpoints, CORS, authentication
- **Debug**: Check request/response details

### Hot Reload Not Working
- **Check**: Frontend container logs
- **Fix**: Restart development container
- **Debug**: Verify source mounting

## 📊 Log Commands

```bash
# Development logs
docker-compose -f docker-compose.dev.yml logs -f cacherr-dev

# Production logs
docker-compose logs -f cacherr-unraid

# Backend only (filter npm output)
docker-compose -f docker-compose.dev.yml logs -f cacherr-dev | grep -v 'npm'
```

## 🔧 Environment Variables for Debugging

```bash
# Add to .env file
DEBUG=true
LOG_LEVEL=DEBUG
RUN_MODE=development
```

## 🚨 Emergency Commands

```bash
# Check container status
docker-compose ps

# Restart container
docker-compose restart cacherr-unraid

# Rebuild container
docker-compose build --no-cache

# Check system resources
docker stats
```

## 📱 Mobile Debugging

- Use Chrome DevTools Device Mode
- Test responsive design
- Check mobile-specific issues

## 🎨 React Developer Tools

- Install Chrome extension
- Inspect component tree
- Monitor props and state
- Profile performance

---

**💡 Pro Tip**: Always use development mode (`./dev-start.sh`) for active debugging. Production mode is for testing the final build only.
