#!/bin/bash
# Automated backup script for Cacherr refactoring
# This script creates backups of critical files before each refactoring phase

PHASE=$1
BACKUP_DIR="./backups/phase_${PHASE}"

if [ -z "$PHASE" ]; then
    echo "Usage: ./create_backup.sh <phase_number>"
    echo "Example: ./create_backup.sh 1"
    echo ""
    echo "Available phases:"
    echo "  1 - Backend fixes (API routes, app configuration)"
    echo "  2 - Settings implementation (React components, routing)"
    echo "  3 - Configuration changes (Pydantic models, imports)"
    echo "  test - Test the backup functionality"
    exit 1
fi

echo "Creating backup for Phase $PHASE..."
mkdir -p "$BACKUP_DIR"

# Phase-specific backups
case $PHASE in
    1)
        echo "Phase 1: Creating backups of backend files..."
        # Backend API and app files
        cp src/web/routes/api.py "$BACKUP_DIR/api.py.bak" 2>/dev/null || echo "Warning: api.py not found"
        cp src/web/app.py "$BACKUP_DIR/app.py.bak" 2>/dev/null || echo "Warning: app.py not found"

        # Docker configuration
        cp Dockerfile "$BACKUP_DIR/Dockerfile.bak" 2>/dev/null || echo "Warning: Dockerfile not found"
        cp docker-compose.yml "$BACKUP_DIR/docker-compose.yml.bak" 2>/dev/null || echo "Warning: docker-compose.yml not found"

        echo "Phase 1 backup complete"
        ;;
    2)
        echo "Phase 2: Creating backups of frontend files..."
        # Frontend React files
        cp frontend/src/App.tsx "$BACKUP_DIR/App.tsx.bak" 2>/dev/null || echo "Warning: App.tsx not found"
        cp frontend/package.json "$BACKUP_DIR/package.json.bak" 2>/dev/null || echo "Warning: package.json not found"

        echo "Phase 2 backup complete"
        ;;
    3)
        echo "Phase 3: Creating backups of configuration files..."
        # Configuration directory
        if [ -d "src/config" ]; then
            cp -r src/config/ "$BACKUP_DIR/config.backup/" 2>/dev/null || echo "Warning: config directory backup failed"
        else
            echo "Warning: src/config directory not found"
        fi

        # Find and backup files that import configuration
        echo "Finding files that import configuration..."
        find . -name "*.py" -exec grep -l "from.*config\|import.*config" {} \; 2>/dev/null | while read -r file; do
            if [[ "$file" != *".bak" ]] && [[ "$file" != *".backup"* ]]; then
                backup_path="$BACKUP_DIR/$(basename "$file").bak"
                cp "$file" "$backup_path" 2>/dev/null && echo "Backed up: $file"
            fi
        done

        echo "Phase 3 backup complete"
        ;;
    test)
        echo "Test mode: Creating test backup..."
        # Create a simple test file for backup testing
        echo "This is a test file for backup verification" > test_backup_file.txt
        cp test_backup_file.txt "$BACKUP_DIR/test_backup_file.txt.bak"
        echo "Test backup created in $BACKUP_DIR"
        ;;
    *)
        echo "Unknown phase: $PHASE"
        echo "Available phases: 1, 2, 3, test"
        exit 1
        ;;
esac

echo "Backup created in $BACKUP_DIR"
echo "To verify backup contents: ls -la $BACKUP_DIR"
echo ""
echo "To restore from backup, use the commands in ROLLBACK_PROCEDURES.md"
