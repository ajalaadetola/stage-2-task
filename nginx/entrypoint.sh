#!/bin/sh

# Substitute environment variables in nginx config
set -e

echo "Starting Nginx configuration..."
envsubst '${PORT}' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf

echo "Nginx configuration completed. Starting Nginx..."
exec "$@"
