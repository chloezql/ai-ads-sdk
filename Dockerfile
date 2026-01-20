# Multi-stage build for AI Ads Core
# Stage 1: Build SDK
FROM node:18-alpine AS sdk-builder

WORKDIR /app

# Copy SDK files
COPY apps/sdk/package*.json ./apps/sdk/
COPY apps/sdk/tsconfig.json ./apps/sdk/
COPY apps/sdk/src ./apps/sdk/src

# Install SDK dependencies and build
WORKDIR /app/apps/sdk
RUN npm install && npm run build

# Stage 2: Python backend
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy Python requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY apps/backend ./apps/backend

# Copy built SDK from builder stage
COPY --from=sdk-builder /app/apps/sdk/dist ./apps/sdk/dist

# Copy assets
COPY assets ./assets

# Copy start script
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Expose port (Railway sets PORT env var)
EXPOSE 8000

# Start command
CMD ["/app/start.sh"]

