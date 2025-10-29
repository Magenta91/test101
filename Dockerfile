# Railway Dockerfile with Tesseract OCR
FROM python:3.10-slim

# Install system dependencies including Tesseract
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    libtesseract-dev \
    libleptonica-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set Tesseract data path
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata/

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Copy startup script
COPY start.sh .
RUN chmod +x start.sh

# Start command
CMD ["./start.sh"]