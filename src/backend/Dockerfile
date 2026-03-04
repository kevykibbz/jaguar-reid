# Backend Dockerfile for Jaguar Re-ID System
# syntax=docker/dockerfile:1
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch CPU version (optimized for Azure deployment)
# Use cache mount to speed up pip downloads
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cpu

# Copy requirements file
COPY requirements.txt .

# Install remaining Python dependencies with cache mount
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# Copy only necessary application code (exclude large model files, notebooks, etc.)
COPY config.py .
COPY models.py .
COPY preprocessing.py .
COPY species_classifier.py .
COPY main.py .
COPY requirements.txt .
COPY animal_filter.py .

# Copy only required models
COPY models/stage1_bigcat_efficientnet_b2.pth models/
COPY models/stage2_species_efficientnet_b2.pth models/
COPY models/mappings/ models/mappings/

# Copy API and utilities
COPY api/ api/
COPY utils/ utils/
COPY database/ database/

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
