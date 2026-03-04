#!/bin/sh
# Entrypoint script to substitute environment variables in nginx config

# Set default backend URL if not provided
BACKEND_URL=${BACKEND_URL:-http://backend:8000}

echo "Configuring nginx with BACKEND_URL: $BACKEND_URL"

# Use sed to substitute BACKEND_URL (avoiding envsubst which interferes with $uri)
sed "s|\${BACKEND_URL}|${BACKEND_URL}|g" /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf

# Debug: show the generated config
echo "================================="
echo "Generated nginx config (line 13):"
echo "================================="
head -n 20 /etc/nginx/conf.d/default.conf | tail -n 10

# Test nginx configuration
echo "Testing nginx configuration..."
nginx -t || (echo "Config test failed! Full config:"; cat /etc/nginx/conf.d/default.conf; exit 1)

echo "Nginx configuration valid, starting server..."
# Start nginx
exec nginx -g 'daemon off;'
