#!/bin/bash
# Cleanup script for deployment preparation

echo "==================================================================="
echo "  DEPLOYMENT CLEANUP SCRIPT"
echo "==================================================================="
echo ""

# Remove test screenshots
if [ -d "screenshots" ]; then
    echo "📸 Removing test screenshots folder (2.8MB)..."
    rm -rf screenshots/
    echo "   ✅ Removed: screenshots/"
fi

# Remove test data files
echo ""
echo "📄 Removing test data files..."
for file in ci_competitive_report.txt ci_competitive_report_NEW.txt ci_competitor_urls.txt ci_competitor_urls_NEW.txt; do
    if [ -f "$file" ]; then
        rm -f "$file"
        echo "   ✅ Removed: $file"
    fi
done

# Check for .env (warn, don't delete)
if [ -f ".env" ]; then
    echo ""
    echo "⚠️  WARNING: .env file exists with secrets!"
    echo "   This file should NOT be deployed."
    echo "   It's already in .gitignore, but verify it won't be pushed."
fi

# Remove Python cache files (if any)
echo ""
echo "🐍 Removing Python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
echo "   ✅ Python cache cleaned"

# Remove pytest cache
if [ -d ".pytest_cache" ]; then
    rm -rf .pytest_cache
    echo "   ✅ Removed: .pytest_cache"
fi

echo ""
echo "==================================================================="
echo "  CLEANUP COMPLETE!"
echo "==================================================================="
echo ""
echo "✅ Repository is now clean and ready for deployment"
echo ""
echo "Next steps:"
echo "  1. Verify .env is not included in deployments"
echo "  2. Review infrastructure/deploy.sh"
echo "  3. Update environment variables in AWS"
echo "  4. Run deployment script"
echo ""
