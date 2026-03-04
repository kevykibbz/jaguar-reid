# Frontend Dockerfile for Jaguar Re-ID System
# Multi-stage build for optimized production image

# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Build argument for API URL (must be declared before COPY to use in build)
ARG VITE_API_URL=/api

# Copy source code
COPY . .

# Set as environment variable for Vite build
ENV VITE_API_URL=$VITE_API_URL

# Debug: Show what API URL is being used
RUN echo "Building with VITE_API_URL=$VITE_API_URL"

# Build the application
RUN npm run build

# Debug: Verify the built API URL in the compiled code
RUN echo "Checking compiled API URL..." && \
    grep -r "VITE_API_URL\|localhost:8000\|/api" /app/dist/assets/*.js | head -5 || echo "No matches found"

# Stage 2: Production
FROM nginx:alpine

# Install envsubst (required for environment variable substitution in nginx config)
RUN apk add --no-cache gettext

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration template and entrypoint script
COPY nginx.conf.template /etc/nginx/conf.d/default.conf.template
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose port
EXPOSE 80

# Use entrypoint script to configure nginx with environment variables
ENTRYPOINT ["/entrypoint.sh"]
