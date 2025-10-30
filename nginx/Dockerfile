FROM nginx:alpine

# Install envsubst
RUN apk add --no-cache gettext

# Copy configuration files
COPY nginx.conf.template /etc/nginx/nginx.conf.template
COPY entrypoint.sh /entrypoint.sh

# Make entrypoint executable and fix line endings (important for Windows)
RUN sed -i 's/\r$//' /entrypoint.sh && \
    chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
