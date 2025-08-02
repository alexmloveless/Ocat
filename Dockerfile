# Multi-stage Dockerfile for Ocat
FROM python:3.12-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Configure Poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Set work directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Development stage
FROM base as dev
# Install all dependencies including dev dependencies
RUN poetry install && rm -rf $POETRY_CACHE_DIR

# Copy source code
COPY . .

# Set entrypoint for development
ENTRYPOINT ["poetry", "run", "ocat"]

# Production stage
FROM base as prod
# Install only main dependencies
RUN poetry install --only=main && rm -rf $POETRY_CACHE_DIR

# Create non-root user
RUN groupadd -r ocat && useradd -r -g ocat ocat

# Copy source code
COPY --chown=ocat:ocat . .

# Create directories for volumes
RUN mkdir -p /app/vector_stores /home/ocat/.ocat && \
    chown -R ocat:ocat /app/vector_stores /home/ocat/.ocat

# Switch to non-root user
USER ocat

# Set environment variables for configuration paths
ENV OCAT_VECTOR_STORE_PATH=/app/vector_stores/default \
    HOME=/home/ocat

# Disable ChromaDB telemetry and tokenizers parallelism
ENV ANONYMIZED_TELEMETRY=False \
    TOKENIZERS_PARALLELISM=false

# Add labels
LABEL org.opencontainers.image.title="Ocat" \
      org.opencontainers.image.description="Interactive LLM Chat CLI tool" \
      org.opencontainers.image.version="0.3.0" \
      org.opencontainers.image.authors="Alex Loveless <alex@alexloveless.uk>"

# Set entrypoint
ENTRYPOINT ["poetry", "run", "ocat"]
