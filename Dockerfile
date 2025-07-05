# ---------- Stage 1: Build dependencies ----------
FROM python:3.13-slim AS builder

# Create app directory
WORKDIR /app

# Prevent Python from writing .pyc files and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Upgrade pip
RUN pip install --upgrade pip

# Copy requirements first (to use caching)
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# ---------- Stage 2: Final production image ----------
FROM python:3.13-slim

# Create user and app directory
RUN useradd -m -r appuser && mkdir /app && chown -R appuser /app

# Set workdir
WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy entire project
COPY --chown=appuser:appuser . .

# Environment settings
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Switch to non-root user
USER appuser

# Run entrypoint script
ENTRYPOINT ["/app/entrypoint.prod.sh"]
