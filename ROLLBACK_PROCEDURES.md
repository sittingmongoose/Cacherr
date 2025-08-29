# 🔄 CACHERR REFACTORING ROLLBACK PROCEDURES

## Overview
This document provides comprehensive rollback procedures for the Cacherr refactoring project. In case of critical failures during refactoring, these procedures ensure the application can be restored to a working state with minimal data loss.

## Critical File Backups
Before each phase, create backups of these critical files:

### Phase 1 Backups (Backend Fixes)
- `src/web/routes/api.py` → `src/web/routes/api.py.phase1.bak`
- `src/web/app.py` → `src/web/app.py.phase1.bak`
- `Dockerfile` → `Dockerfile.phase1.bak`
- `docker-compose.yml` → `docker-compose.yml.phase1.bak`

### Phase 2 Backups (Settings Implementation)
- `frontend/src/App.tsx` → `frontend/src/App.tsx.phase2.bak`
- `frontend/package.json` → `frontend/package.json.phase2.bak`

### Phase 3 Backups (Configuration Changes)
- `src/config/` → `src/config.phase3.backup/`
- All Python files importing configuration

## Rollback Commands by Phase

### If Phase 1 Fails:
```bash
# Restore backend files
cp src/web/routes/api.py.phase1.bak src/web/routes/api.py
cp src/web/app.py.phase1.bak src/web/app.py
cp Dockerfile.phase1.bak Dockerfile
cp docker-compose.yml.phase1.bak docker-compose.yml

# Restart services
docker-compose down
docker-compose up --build
```

### If Phase 2 Fails:
```bash
# Restore frontend files
cp frontend/src/App.tsx.phase2.bak frontend/src/App.tsx
cp frontend/package.json.phase2.bak frontend/package.json

# Rebuild frontend
cd frontend && npm install && npm run build
```

### If Phase 3 Configuration Fails:
```bash
# Restore entire config directory
rm -rf src/config/
cp -r src/config.phase3.backup/ src/config/

# Restart application
docker-compose restart
```

## Emergency Recovery Commands
If the application becomes completely unresponsive:

1. Stop all containers: `docker-compose down`
2. Remove any corrupted images: `docker system prune -f`
3. Restore from git: `git stash && git checkout HEAD~1`
4. Rebuild: `docker-compose up --build`

## Validation After Rollback
After any rollback:
1. Test dashboard access: http://localhost:5445
2. Verify all tabs load (Dashboard, Cached, Logs)
3. Check for console errors in browser
4. Ensure API health endpoints respond: `/api/health`

## Testing Rollback Procedures

Before starting refactoring, test these procedures:

### Test 1: File Restoration
1. Create a test backup: `./create_backup.sh test`
2. Modify a backed-up file
3. Restore from backup
4. Verify restoration worked

### Test 2: Service Recovery
1. Stop application: `docker-compose down`
2. Start application: `docker-compose up`
3. Verify dashboard loads correctly
4. Test all major functionality

## Contact Information
If rollback procedures fail:
- Check Git commit history: `git log --oneline`
- Consider reverting to last known good commit
- Document any issues encountered for future agents
