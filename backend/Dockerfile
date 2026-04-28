FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy ML pipeline
COPY ../ml_pipeline /app/ml_pipeline

# Copy backend
COPY . /app/backend
WORKDIR /app/backend

RUN pip install --no-cache-dir -r requirements.txt

# Create uploads directory
RUN mkdir -p /app/data/uploads

EXPOSE 8000

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
