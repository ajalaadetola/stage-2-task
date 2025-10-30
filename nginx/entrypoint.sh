#!/bin/sh
set -e

echo "Configuring Nginx with ACTIVE_POOL: ${ACTIVE_POOL}"

# Determine backup pool (whichever isn't active)
if [ "$ACTIVE_POOL" = "blue" ]; then
    BACKUP_POOL="green"
else
    BACKUP_POOL="blue"
fi

export BACKUP_POOL

echo "BACKUP_POOL set to: $BACKUP_POOL"

# Substitute environment variables
envsubst '${PORT},${ACTIVE_POOL} ${BACKUP_POOL}' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf

echo "Nginx configuration completed:"
echo "Active: app_${ACTIVE_POOL}:3000"
echo "Backup: app_${BACKUP_POOL}:3000"
echo "Port: ${PORT}"

# Start Nginx
exec "$@"
