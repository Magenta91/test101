#!/bin/bash
# Railway startup script with debugging

echo "🚀 Starting PDF Extraction Service..."
echo "📍 Current directory: $(pwd)"
echo "📋 Environment variables:"
echo "   PORT: ${PORT:-5000}"
echo "   FLASK_ENV: ${FLASK_ENV:-production}"

# Check if Tesseract is available
echo "🔍 Checking Tesseract installation..."
if command -v tesseract &> /dev/null; then
    echo "✅ Tesseract found: $(which tesseract)"
    tesseract --version | head -1
else
    echo "❌ Tesseract not found"
fi

# Check Python modules
echo "🐍 Checking Python modules..."
python -c "
try:
    import flask, openai, boto3, pandas
    print('✅ Core modules imported successfully')
except ImportError as e:
    print(f'❌ Module import error: {e}')
"

# Start the application
echo "🌐 Starting Gunicorn server..."
exec gunicorn --bind 0.0.0.0:$PORT app:app --timeout 120 --workers 1 --preload --log-level info --access-logfile - --error-logfile -