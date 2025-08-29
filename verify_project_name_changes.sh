#!/bin/bash
# Verification script for project name changes
# This script checks for remaining old project name references that should be updated

echo "🔍 CACHERR PROJECT NAME VERIFICATION SCRIPT"
echo "=============================================="
echo ""

echo "Searching for remaining old project name references..."
echo "=== PlexCacheUltra references ==="
grep -r -i "plexcacheultra" /mnt/user/Cursor/Cacherr/ --exclude-dir=node_modules --exclude-dir=.git --exclude="*.log" --exclude="CACHERR_REFACTORING_MASTER_PLAN.md" --exclude="AGENT_EXECUTION_GUIDE.md" || echo "✅ None found"

echo ""
echo "=== PlexCache references ==="
grep -r -i "plexcache" /mnt/user/Cursor/Cacherr/ --exclude-dir=node_modules --exclude-dir=.git --exclude="*.log" --exclude="CACHERR_REFACTORING_MASTER_PLAN.md" --exclude="AGENT_EXECUTION_GUIDE.md" | grep -v "cacherr" || echo "✅ None found"

echo ""
echo "=== PLEXCACHE environment variable patterns ==="
grep -r "PLEXCACHE" /mnt/user/Cursor/Cacherr/ --exclude-dir=node_modules --exclude-dir=.git --exclude="*.log" --exclude="CACHERR_REFACTORING_MASTER_PLAN.md" --exclude="AGENT_EXECUTION_GUIDE.md" || echo "✅ None found"

echo ""
echo "=== PLEXCACHEULTRA environment variable patterns ==="
grep -r "PLEXCACHEULTRA" /mnt/user/Cursor/Cacherr/ --exclude-dir=node_modules --exclude-dir=.git --exclude="*.log" --exclude="CACHERR_REFACTORING_MASTER_PLAN.md" --exclude="AGENT_EXECUTION_GUIDE.md" || echo "✅ None found"

echo ""
echo "=== Checking for old project references in key files ==="

# Check key user-facing files
files_to_check=(
    "main.py"
    "src/web/app.py"
    "src/web/routes/api.py"
    "src/application.py"
    "src/core/service_configuration.py"
    "frontend/src/services/settingsApi.ts"
    "frontend/src/components/Dashboard/Dashboard.test.tsx"
    "tests/mocks/service_mocks.py"
    "tests/test_secure_cached_files_service.py"
)

for file in "${files_to_check[@]}"; do
    if [ -f "/mnt/user/Cursor/Cacherr/$file" ]; then
        if grep -q -i "plexcache" "/mnt/user/Cursor/Cacherr/$file"; then
            echo "⚠️  Found references in: $file"
        else
            echo "✅ Clean: $file"
        fi
    else
        echo "⚠️  File not found: $file"
    fi
done

echo ""
echo "=== SUMMARY ==="
echo "If no warnings appeared above, all project name references have been successfully updated!"
echo "The project is now consistently named 'Cacherr' throughout the codebase."
