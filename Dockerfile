FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install -r requirements.txt

# Copy application files
COPY . .

# Create uploads directory
RUN mkdir -p uploads

# Expose port (Railway uses $PORT env var, fallback to 8501)
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:${PORT:-8501}/_stcore/health

# Run the application
# Railway injects $PORT dynamically; use shell form to expand the variable
CMD streamlit run app_modern.py \
    --server.port=${PORT:-8501} \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false