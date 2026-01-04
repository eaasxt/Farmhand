#!/bin/bash

# Simple deployment validator for testing
echo "🔍 Running deployment validation..."

# Check basic requirements
echo "Checking Python..."
python3 --version && echo "✅ Python OK" || echo "❌ Python missing"

echo "Checking SQLite..."
sqlite3 -version && echo "✅ SQLite OK" || echo "❌ SQLite missing"

echo "Checking required files..."
for file in requirements.txt setup_marketplace.py; do
    [ -f "$file" ] && echo "✅ $file exists" || echo "❌ $file missing"
done

echo "Checking deployment scripts..."
for script in deployment/scripts/deploy/deploy_meow_stack.sh deployment/scripts/rollback/rollback_meow_stack.sh; do
    [ -x "$script" ] && echo "✅ $script executable" || echo "❌ $script not executable"
done

echo "🎉 Validation completed!"
