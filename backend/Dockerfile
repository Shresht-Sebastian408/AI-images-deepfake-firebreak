# Use official lightweight Python image (3.11 is stable for ML libraries)
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies needed for OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Google Cloud Run expects the app to listen on the port defined by the $PORT env var (default 8080)
# Use shell form CMD so env vars are interpolated
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}
