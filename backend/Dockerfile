FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HF_HOME=/app/models \
    SENTENCE_TRANSFORMERS_HOME=/app/models

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file first for layer caching
COPY backend/requirements.txt /app/backend/requirements.txt

# Install Python packages using CPU wheel index for lightweight size
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy backend code, scripts, and knowledge base
COPY backend /app/backend
COPY knowledge /app/knowledge
COPY .env /app/.env

# Create models directory if it doesn't exist
RUN mkdir -p /app/models

# Expose port 8000
EXPOSE 8000

# Run FastAPI backend service
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
