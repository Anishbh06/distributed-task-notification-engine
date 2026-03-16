# Distributed Task & Notification Engine
FROM python:3.12-slim

# Create non-root user
RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -m -s /bin/bash appuser

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Fix Windows CRLF and set permissions
RUN sed -i 's/\r$//' /app/scripts/entrypoint.sh && \
    chmod +x /app/scripts/entrypoint.sh && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["./scripts/entrypoint.sh"]
