# Build stage
FROM python:3.14-slim AS builder

WORKDIR /build

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Create virtual environment and install dependencies using pip
RUN python -m venv /opt/venv && \
    /opt/venv/bin/python -m pip install --upgrade pip setuptools wheel && \
    /opt/venv/bin/pip install -e . && \
    /opt/venv/bin/pip install uvicorn[standard]

# Runtime stage
FROM python:3.14-slim

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY src/ ./src/

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PROJECT_NAME="Ecommerce FastAPI" \
    API_V1_STR="/api/v1" \
    ACCESS_TOKEN_EXPIRE_MINUTES=11520 \
    DATABASE_URL="sqlite:///./ecommerce.db"

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the application
CMD ["uvicorn", "src.ecommerce_fastapi.main:app", "--host", "0.0.0.0", "--port", "8000"]
