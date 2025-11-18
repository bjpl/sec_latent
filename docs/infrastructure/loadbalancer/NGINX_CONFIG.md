# Nginx Load Balancer Configuration

## Overview

Nginx reverse proxy and load balancer configuration for the SEC Latent platform with SSL/TLS termination, WebSocket support, and advanced features.

## Architecture

```
                    Internet
                       │
                       │ HTTPS (443)
                       │
        ┌──────────────▼──────────────┐
        │   Nginx Load Balancer       │
        │   - SSL/TLS Termination     │
        │   - Load Balancing          │
        │   - Health Checks           │
        │   - Rate Limiting           │
        │   - Caching                 │
        └──────────────┬──────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
┌───────▼────────┐            ┌───────▼────────┐
│   Backend 1    │            │   Backend 2    │
│   :8000        │            │   :8000        │
└────────────────┘            └────────────────┘
```

## Main Configuration

**/etc/nginx/nginx.conf**:
```nginx
user nginx;
worker_processes auto;
worker_rlimit_nofile 65535;

error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 4096;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging format
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for" '
                    'rt=$request_time uct="$upstream_connect_time" '
                    'uht="$upstream_header_time" urt="$upstream_response_time"';

    access_log /var/log/nginx/access.log main;

    # Performance tuning
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    keepalive_requests 100;
    types_hash_max_size 2048;
    server_tokens off;

    # Compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript
               application/json application/javascript application/xml+rss
               application/rss+xml font/truetype font/opentype
               application/vnd.ms-fontobject image/svg+xml;

    # Client settings
    client_max_body_size 100M;
    client_body_buffer_size 128k;
    client_body_timeout 60s;
    client_header_timeout 60s;

    # Proxy settings
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;
    proxy_buffering on;
    proxy_buffer_size 4k;
    proxy_buffers 8 4k;
    proxy_busy_buffers_size 8k;

    # Rate limiting zones
    limit_req_zone $binary_remote_addr zone=general:10m rate=100r/m;
    limit_req_zone $binary_remote_addr zone=api:10m rate=1000r/m;
    limit_req_zone $binary_remote_addr zone=auth:10m rate=5r/m;

    # Connection limiting
    limit_conn_zone $binary_remote_addr zone=addr:10m;

    # Upstream definitions
    include /etc/nginx/conf.d/upstreams/*.conf;

    # Server configurations
    include /etc/nginx/conf.d/*.conf;
}
```

## Upstream Configurations

**/etc/nginx/conf.d/upstreams/backend.conf**:
```nginx
upstream backend_servers {
    least_conn;  # Load balancing algorithm

    # Backend instances
    server backend-1:8000 max_fails=3 fail_timeout=30s weight=1;
    server backend-2:8000 max_fails=3 fail_timeout=30s weight=1;
    server backend-3:8000 max_fails=3 fail_timeout=30s weight=1 backup;

    # Keepalive connections
    keepalive 32;
    keepalive_timeout 60s;
    keepalive_requests 100;

    # Health check (requires nginx-plus or third-party module)
    # check interval=5000 rise=2 fall=3 timeout=1000 type=http;
    # check_http_send "GET /health HTTP/1.0\r\n\r\n";
    # check_http_expect_alive http_2xx http_3xx;
}

upstream frontend_servers {
    least_conn;

    server frontend-1:3000 max_fails=3 fail_timeout=30s;
    server frontend-2:3000 max_fails=3 fail_timeout=30s;

    keepalive 16;
}

upstream websocket_servers {
    ip_hash;  # Sticky sessions for WebSocket

    server backend-1:8000 max_fails=3 fail_timeout=30s;
    server backend-2:8000 max_fails=3 fail_timeout=30s;

    keepalive 32;
}
```

## SSL/TLS Configuration

**/etc/nginx/conf.d/ssl.conf**:
```nginx
# SSL session cache
ssl_session_cache shared:SSL:50m;
ssl_session_timeout 1d;
ssl_session_tickets off;

# Modern SSL configuration
ssl_protocols TLSv1.3;
ssl_ciphers 'TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256:TLS_AES_128_GCM_SHA256';
ssl_prefer_server_ciphers off;

# OCSP stapling
ssl_stapling on;
ssl_stapling_verify on;
ssl_trusted_certificate /etc/nginx/ssl/chain.pem;
resolver 8.8.8.8 8.8.4.4 valid=300s;
resolver_timeout 5s;

# SSL certificate paths (managed by certbot)
ssl_certificate /etc/letsencrypt/live/api.sec-latent.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/api.sec-latent.com/privkey.pem;
```

## Server Blocks

**/etc/nginx/conf.d/api.sec-latent.com.conf**:
```nginx
# Redirect HTTP to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name api.sec-latent.com;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.sec-latent.com;

    # SSL configuration
    include /etc/nginx/conf.d/ssl.conf;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';" always;

    # Rate limiting
    limit_req zone=general burst=20 nodelay;
    limit_conn addr 10;

    # Health check endpoint (no rate limit)
    location /health {
        access_log off;
        proxy_pass http://backend_servers;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Metrics endpoint (internal only)
    location /metrics {
        allow 10.0.0.0/8;
        deny all;
        access_log off;
        proxy_pass http://backend_servers;
    }

    # API endpoints
    location /api/ {
        limit_req zone=api burst=50 nodelay;

        proxy_pass http://backend_servers;
        proxy_http_version 1.1;

        # Proxy headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Request-ID $request_id;

        # Keepalive
        proxy_set_header Connection "";

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # Buffering
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;

        # Cache (for GET requests only)
        proxy_cache api_cache;
        proxy_cache_valid 200 5m;
        proxy_cache_valid 404 1m;
        proxy_cache_bypass $http_cache_control;
        add_header X-Cache-Status $upstream_cache_status;
    }

    # WebSocket endpoint
    location /ws/ {
        proxy_pass http://websocket_servers;
        proxy_http_version 1.1;

        # WebSocket headers
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket timeouts (longer)
        proxy_connect_timeout 7d;
        proxy_send_timeout 7d;
        proxy_read_timeout 7d;
    }

    # Authentication endpoint (strict rate limit)
    location /auth/ {
        limit_req zone=auth burst=2 nodelay;

        proxy_pass http://backend_servers;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files (if any)
    location /static/ {
        alias /var/www/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Error pages
    error_page 502 503 504 /50x.html;
    location = /50x.html {
        root /usr/share/nginx/html;
    }
}
```

## Caching Configuration

**/etc/nginx/conf.d/cache.conf**:
```nginx
# Cache paths
proxy_cache_path /var/cache/nginx/api
                 levels=1:2
                 keys_zone=api_cache:10m
                 max_size=1g
                 inactive=60m
                 use_temp_path=off;

proxy_cache_path /var/cache/nginx/static
                 levels=1:2
                 keys_zone=static_cache:10m
                 max_size=5g
                 inactive=30d
                 use_temp_path=off;

# Cache key
proxy_cache_key "$scheme$request_method$host$request_uri";

# Cache bypass conditions
map $http_cache_control $bypass_cache {
    "no-cache" 1;
    "private" 1;
    default 0;
}
```

## Docker Deployment

**/docker/Dockerfile.nginx**:
```dockerfile
FROM nginx:1.25-alpine

# Install additional modules
RUN apk add --no-cache openssl

# Copy configuration
COPY config/nginx/nginx.conf /etc/nginx/nginx.conf
COPY config/nginx/conf.d /etc/nginx/conf.d

# Create cache directories
RUN mkdir -p /var/cache/nginx/api \
             /var/cache/nginx/static \
             /var/www/certbot

# Create log directory
RUN mkdir -p /var/log/nginx

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/health || exit 1

# Expose ports
EXPOSE 80 443

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
```

**/docker/docker-compose.yml** addition:
```yaml
nginx:
  build:
    context: ..
    dockerfile: docker/Dockerfile.nginx
  container_name: sec-latent-nginx
  depends_on:
    - backend
    - frontend
  volumes:
    - ./config/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    - ./config/nginx/conf.d:/etc/nginx/conf.d:ro
    - nginx-cache:/var/cache/nginx
    - certbot-data:/etc/letsencrypt
    - certbot-www:/var/www/certbot
  ports:
    - "80:80"
    - "443:443"
  networks:
    - sec-latent-network
  restart: unless-stopped

certbot:
  image: certbot/certbot:latest
  container_name: sec-latent-certbot
  volumes:
    - certbot-data:/etc/letsencrypt
    - certbot-www:/var/www/certbot
  command: certonly --webroot --webroot-path=/var/www/certbot
           --email admin@sec-latent.com --agree-tos --no-eff-email
           -d api.sec-latent.com
  networks:
    - sec-latent-network

volumes:
  nginx-cache:
  certbot-data:
  certbot-www:
```

## SSL Certificate Management

**/scripts/renew-ssl.sh**:
```bash
#!/bin/bash
# Automatic SSL certificate renewal

# Renew certificates
docker-compose run --rm certbot renew

# Reload nginx
docker-compose exec nginx nginx -s reload

echo "SSL certificates renewed and nginx reloaded"
```

**Cron job** (monthly renewal):
```cron
0 0 1 * * /scripts/renew-ssl.sh >> /var/log/ssl-renewal.log 2>&1
```

## Health Check Script

**/scripts/check-nginx.sh**:
```bash
#!/bin/bash
# Nginx health check script

# Check if nginx is running
if ! docker-compose ps nginx | grep -q "Up"; then
    echo "ERROR: Nginx is not running"
    exit 1
fi

# Check HTTP response
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/health)
if [ "$HTTP_STATUS" -ne 200 ]; then
    echo "ERROR: Health check failed with status $HTTP_STATUS"
    exit 1
fi

# Check HTTPS response
HTTPS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://api.sec-latent.com/health)
if [ "$HTTPS_STATUS" -ne 200 ]; then
    echo "ERROR: HTTPS health check failed with status $HTTPS_STATUS"
    exit 1
fi

# Check SSL certificate expiry
EXPIRY_DATE=$(echo | openssl s_client -servername api.sec-latent.com \
              -connect api.sec-latent.com:443 2>/dev/null | \
              openssl x509 -noout -enddate | cut -d= -f2)

EXPIRY_EPOCH=$(date -d "$EXPIRY_DATE" +%s)
NOW_EPOCH=$(date +%s)
DAYS_UNTIL_EXPIRY=$(( ($EXPIRY_EPOCH - $NOW_EPOCH) / 86400 ))

if [ $DAYS_UNTIL_EXPIRY -lt 30 ]; then
    echo "WARNING: SSL certificate expires in $DAYS_UNTIL_EXPIRY days"
fi

echo "Nginx health check passed"
echo "SSL certificate expires in $DAYS_UNTIL_EXPIRY days"
```

## Monitoring

### Nginx Prometheus Exporter

**/docker/docker-compose.yml** addition:
```yaml
nginx-exporter:
  image: nginx/nginx-prometheus-exporter:latest
  container_name: sec-latent-nginx-exporter
  command:
    - -nginx.scrape-uri=http://nginx:8080/stub_status
  ports:
    - "9113:9113"
  networks:
    - sec-latent-network
  depends_on:
    - nginx
```

### Stub Status Configuration

Add to nginx.conf:
```nginx
server {
    listen 8080;
    server_name localhost;

    location /stub_status {
        stub_status on;
        access_log off;
        allow 127.0.0.1;
        allow 10.0.0.0/8;
        deny all;
    }
}
```

## Log Rotation

**/etc/logrotate.d/nginx**:
```
/var/log/nginx/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 nginx nginx
    sharedscripts
    postrotate
        if [ -f /var/run/nginx.pid ]; then
            kill -USR1 `cat /var/run/nginx.pid`
        fi
    endscript
}
```

## Performance Tuning

### TCP Optimization

**/etc/sysctl.conf**:
```
# Increase TCP buffer sizes
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216

# Increase connection backlog
net.core.somaxconn = 4096
net.ipv4.tcp_max_syn_backlog = 8192

# TCP optimization
net.ipv4.tcp_fin_timeout = 15
net.ipv4.tcp_keepalive_time = 300
net.ipv4.tcp_keepalive_probes = 5
net.ipv4.tcp_keepalive_intvl = 15

# Increase file descriptors
fs.file-max = 65535
```

### File Descriptor Limits

**/etc/security/limits.conf**:
```
nginx soft nofile 65535
nginx hard nofile 65535
```

## Troubleshooting

### Test Configuration
```bash
# Test nginx configuration
docker-compose exec nginx nginx -t

# Reload configuration
docker-compose exec nginx nginx -s reload

# View error log
docker-compose logs nginx --tail=100 -f
```

### Check Upstream Health
```bash
# Check backend connectivity
docker-compose exec nginx curl -I http://backend:8000/health

# Check upstream status
docker-compose exec nginx cat /var/log/nginx/access.log | \
    grep -E "upstream|backend" | tail -20
```

### Analyze Performance
```bash
# Request rate
awk '{print $4}' /var/log/nginx/access.log | cut -d: -f1 | \
    sort | uniq -c | sort -rn | head

# Response times
awk '{print $NF}' /var/log/nginx/access.log | \
    awk '{sum+=$1; count++} END {print "Average:", sum/count}'

# Error rate
grep " 5[0-9][0-9] " /var/log/nginx/access.log | wc -l
```

## Best Practices

1. **Security**
   - Always use TLS 1.3
   - Implement rate limiting
   - Add security headers
   - Regular SSL certificate rotation

2. **Performance**
   - Enable gzip compression
   - Use keepalive connections
   - Configure appropriate buffer sizes
   - Implement caching where appropriate

3. **Reliability**
   - Configure health checks
   - Set appropriate timeouts
   - Use multiple upstream servers
   - Enable connection limiting

4. **Monitoring**
   - Export metrics to Prometheus
   - Log rotation configured
   - Alert on error rates
   - Track response times

5. **Maintenance**
   - Regular log analysis
   - Configuration testing before reload
   - SSL certificate monitoring
   - Capacity planning
