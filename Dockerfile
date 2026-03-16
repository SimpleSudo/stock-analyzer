# Multi-stage build
# Stage 1: Build frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# Stage 2: Build backend
FROM python:3.11-slim AS backend-builder
WORKDIR /app/backend
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
# Create a non-root user
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# Stage 3: Production
FROM python:3.11-slim
WORKDIR /app
# Install runtime dependencies
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-builder /app/backend ./backend
# Copy frontend build
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist
# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
USER appuser
# Expose port
EXPOSE 8000
# Command to run
CMD ["uvicorn", "backend.src.main:app", "--host", "0.0.0.0", "--port", "8000"]
