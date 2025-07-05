# ---------- Stage 1: Build dependencies ----------
FROM python:3.10-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    libffi-dev \
    libssl-dev \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only requirements for caching
COPY requirements.txt .

# Upgrade pip
RUN python -m pip install --upgrade pip

# Install Python dependencies to a separate prefix
RUN pip install --prefix=/install -r requirements.txt

# ---------- Stage 2: Final production image ----------
FROM python:3.10-slim

# Copy installed dependencies from builder stage
COPY --from=builder /install /usr/local

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -r appuser

WORKDIR /app

# Copy project source code
COPY . .

# Make entrypoint script executable
RUN chmod +x /app/entrypoint.prod.sh

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Switch to non-root user
USER appuser

# Expose the app port
EXPOSE 8000

# Use the entrypoint script to start container
ENTRYPOINT ["/app/entrypoint.prod.sh"]
