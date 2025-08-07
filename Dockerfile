# Use Python 3.12 slim image (latest with OpenAI Agents support)
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies for AWS Linux compatibility
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Clean up requirements.txt - remove standard library modules that shouldn't be in requirements
RUN sed -i '/^asyncio$/d' requirements.txt && \
    sed -i '/^uuid$/d' requirements.txt && \
    sed -i '/^datetime$/d' requirements.txt && \
    sed -i '/^typing$/d' requirements.txt && \
    sed -i '/^dataclasses$/d' requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY examples/ ./examples/
COPY ai-agents-implementation/ ./ai-agents-implementation/

# Create sessions directory for SQLite databases
RUN mkdir -p sessions

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose Streamlit default port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Set environment variables for production
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ENABLE_CORS=false
ENV STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false
ENV PYTHONPATH=/app

# Default command to run Streamlit app
CMD ["streamlit", "run", "examples/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]