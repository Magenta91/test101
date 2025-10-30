# Ubuntu-based Dockerfile for better library compatibility
FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install Python and system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3.10-dev \
    python3-pip \
    tesseract-ocr \
    tesseract-ocr-eng \
    libtesseract-dev \
    libleptonica-dev \
    pkg-config \
    libssl3 \
    libffi8 \
    libcrypt1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set Tesseract data path
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata/

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir --upgrade pip
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set default port
ENV PORT=8080

# Start command
CMD python3 -m gunicorn --bind 0.0.0.0:$PORT app:app --timeout 120 --workers 1 --preload --log-level info