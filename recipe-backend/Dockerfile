FROM python:3.9-slim

# Add build argument for OLLAMA_HOST
ARG OLLAMA_HOST="http://34.173.253.123:11434"

# Install system dependencies
RUN apt-get update && \
    apt-get install -y \
    curl \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p /app/ai

# Copy the CSV file first and ensure it exists
COPY ai/Food*.csv /app/ai/
RUN test -f /app/ai/"Food Ingredients and Recipe Dataset with Image Name Mapping.csv" || exit 1

# Copy the rest of the application code
COPY . .

# Set environment variables
ENV PORT=8080
ENV OLLAMA_HOST=${OLLAMA_HOST}
ENV PYTHONUNBUFFERED=1

# Verify files exist
RUN ls -la /app/ai/

# Create cache directory
RUN mkdir -p /app/cache/usda

EXPOSE ${PORT}

# Simple uvicorn command without timeouts
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]



