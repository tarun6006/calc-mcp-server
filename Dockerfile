# Use Python 3.13 slim image for smaller size and better performance
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Create .env file template (will be overridden by environment variables)
RUN echo "# Calculator MCP Server Environment Variables" > .env && \
    echo "CALC_SERVER_NAME=calculator-server" >> .env && \
    echo "CALC_SERVER_VERSION=1.0" >> .env && \
    echo "CALC_PRECISION=10" >> .env && \
    echo "CALC_MAX_VALUE=1e15" >> .env && \
    echo "LOG_LEVEL=INFO" >> .env

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Expose port (Google Cloud Run uses PORT environment variable)
EXPOSE 8080

# Health check for SSE-enabled calculator server
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; r=requests.get('http://localhost:8080/health', timeout=10); exit(0 if r.status_code==200 and r.json().get('status')=='healthy' else 1)"

# Use gunicorn for production deployment with SSE support
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "8", "--timeout", "120", "--keep-alive", "5", "--access-logfile", "-", "--error-logfile", "-", "--worker-class", "gevent", "app:app"]