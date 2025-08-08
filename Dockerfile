# Use Python 3.13.6 Alpine 3.21 image - no CVEs and most secure
FROM python:3.13.6-alpine3.21

# Set working directory
WORKDIR /app

# Update system packages and install build dependencies for Alpine
RUN apk update && \
    apk upgrade && \
    apk add --no-cache gcc musl-dev && \
    rm -rf /var/cache/apk/*

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

# Create non-root user for security (Alpine syntax)
RUN addgroup -g 1000 app && \
    adduser -u 1000 -G app -s /bin/sh -D app && \
    chown -R app:app /app
USER app

# Expose port (Google Cloud Run uses PORT environment variable)
EXPOSE 8080

# Note: Google Cloud Run handles health checks automatically
# No custom HEALTHCHECK needed - Cloud Run probes the service directly

# Use gunicorn with sync worker and threads for reliable SSE performance
# This avoids eventlet compatibility issues while maintaining SSE functionality
CMD gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 1 --threads 16 --timeout 120 --keep-alive 5 --access-logfile - --error-logfile - --worker-class sync app:app
