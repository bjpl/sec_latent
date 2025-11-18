# Railway Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the SEC Latent platform to Railway with production-grade configuration.

## Prerequisites

- Railway account (sign up at https://railway.app)
- GitHub repository connected to Railway
- Domain name for production (optional)
- Environment variables prepared

## Railway Project Structure

```
sec-latent/
├── Frontend Service (Next.js)
├── Backend Service (FastAPI)
├── Worker Service (Celery)
├── Beat Service (Celery Beat)
├── PostgreSQL Database
└── Redis Cache
```

## Step-by-Step Deployment

### 1. Create Railway Project

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Create new project
railway init

# Link to GitHub repository
railway link
```

### 2. Add PostgreSQL Database

```bash
# Add PostgreSQL plugin
railway add --database postgres

# Get database URL
railway variables

# Should see: DATABASE_URL=postgresql://...
```

### 3. Add Redis Cache

```bash
# Add Redis plugin
railway add --database redis

# Get Redis URL
railway variables

# Should see: REDIS_URL=redis://...
```

### 4. Configure Environment Variables

Create `.railway.env` file:

```env
# Application
ENVIRONMENT=production
DEBUG=false

# Database (auto-populated by Railway)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Redis (auto-populated by Railway)
REDIS_URL=${{Redis.REDIS_URL}}

# Celery
CELERY_BROKER_URL=${{Redis.REDIS_URL}}/0
CELERY_RESULT_BACKEND=${{Redis.REDIS_URL}}/0
CELERY_WORKER_CONCURRENCY=4

# SEC Edgar
SEC_USER_AGENT=SEC-Latent/1.0 (contact@yourdomain.com)
SEC_RATE_LIMIT=10
SEC_TIMEOUT=30

# Claude API
SONNET_ENDPOINT=https://api.anthropic.com/v1/complete
SONNET_API_KEY=your-sonnet-api-key
HAIKU_ENDPOINT=https://api.anthropic.com/v1/complete
HAIKU_API_KEY=your-haiku-api-key

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Monitoring
SENTRY_DSN=https://...@sentry.io/...
LOG_LEVEL=INFO
ENABLE_METRICS=true

# Security
JWT_SECRET_KEY=$(openssl rand -hex 32)
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### 5. Deploy Backend Service

Create `railway.backend.json`:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "docker/Dockerfile.backend"
  },
  "deploy": {
    "numReplicas": 2,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 3,
    "healthcheckPath": "/health",
    "healthcheckTimeout": 10,
    "startCommand": "gunicorn src.api.main:app --bind 0.0.0.0:$PORT --workers 4 --worker-class uvicorn.workers.UvicornWorker --timeout 120"
  },
  "resources": {
    "cpu": 1.0,
    "memory": 2048
  }
}
```

Deploy:

```bash
railway up --service backend --config railway.backend.json
```

### 6. Deploy Frontend Service

Create `railway.frontend.json`:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "docker/Dockerfile.frontend"
  },
  "deploy": {
    "numReplicas": 2,
    "restartPolicyType": "ON_FAILURE",
    "healthcheckPath": "/api/health",
    "healthcheckTimeout": 10,
    "startCommand": "npm start"
  },
  "resources": {
    "cpu": 0.5,
    "memory": 512
  }
}
```

Deploy:

```bash
railway up --service frontend --config railway.frontend.json
```

### 7. Deploy Worker Service

Create `railway.worker.json`:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "docker/Dockerfile.worker"
  },
  "deploy": {
    "numReplicas": 2,
    "restartPolicyType": "ON_FAILURE",
    "startCommand": "celery -A src.pipeline.celery_tasks worker --loglevel=info --concurrency=4"
  },
  "resources": {
    "cpu": 2.0,
    "memory": 4096
  }
}
```

Deploy:

```bash
railway up --service worker --config railway.worker.json
```

### 8. Deploy Beat Scheduler

Create `railway.beat.json`:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "docker/Dockerfile.worker"
  },
  "deploy": {
    "numReplicas": 1,
    "restartPolicyType": "ON_FAILURE",
    "startCommand": "celery -A src.pipeline.celery_tasks beat --loglevel=info"
  },
  "resources": {
    "cpu": 0.25,
    "memory": 256
  }
}
```

Deploy:

```bash
railway up --service beat --config railway.beat.json
```

## Custom Domain Configuration

### 1. Add Custom Domain in Railway Dashboard

1. Go to your service in Railway dashboard
2. Click "Settings" > "Domains"
3. Click "Custom Domain"
4. Enter your domain (e.g., `api.yourdomain.com`)

### 2. Configure DNS

Add CNAME record in your DNS provider:

```
Type: CNAME
Name: api
Value: your-project.up.railway.app
TTL: 300
```

For root domain, use ALIAS or ANAME:

```
Type: ALIAS
Name: @
Value: your-project.up.railway.app
TTL: 300
```

### 3. SSL/TLS Certificate

Railway automatically provisions Let's Encrypt SSL certificates. No manual configuration needed.

## Monitoring Setup

### 1. Railway Dashboard

Built-in monitoring includes:
- CPU and memory usage
- Request metrics
- Deployment logs
- Health check status

### 2. External Monitoring (Sentry)

Already configured via `SENTRY_DSN` environment variable. Verify:

```bash
railway logs --service backend | grep "Sentry initialized"
```

### 3. Uptime Monitoring

Add uptime monitoring with:
- Railway's built-in health checks
- External service (e.g., UptimeRobot, Pingdom)
- Check `/health` endpoint every 5 minutes

## Database Management

### 1. Access PostgreSQL

```bash
# Get database URL
railway variables --service postgres

# Connect via psql
railway connect postgres

# Or use connection string
psql $(railway variables --service postgres | grep DATABASE_URL)
```

### 2. Database Backups

Railway automatically backs up PostgreSQL daily. To manually backup:

```bash
# Export database
railway run --service postgres pg_dump > backup.sql

# Restore database
railway run --service postgres psql < backup.sql
```

### 3. Database Migrations

```bash
# Run Alembic migrations
railway run --service backend alembic upgrade head
```

## Scaling Configuration

### 1. Horizontal Scaling

Scale services via Railway dashboard or CLI:

```bash
# Scale backend to 4 replicas
railway scale backend --replicas 4

# Scale worker to 8 replicas
railway scale worker --replicas 8
```

### 2. Vertical Scaling

Adjust resources in Railway dashboard:

1. Go to service settings
2. Adjust CPU and memory
3. Click "Save"
4. Service will restart with new resources

### 3. Auto-Scaling Rules

Configure in `railway.json`:

```json
{
  "autoscaling": {
    "enabled": true,
    "minReplicas": 2,
    "maxReplicas": 6,
    "targetCPUUtilizationPercentage": 70,
    "targetMemoryUtilizationPercentage": 80
  }
}
```

## Deployment Strategies

### 1. Blue-Green Deployment

Railway supports zero-downtime deployments by default:

1. New version deployed alongside old version
2. Health checks verify new version
3. Traffic automatically switched
4. Old version kept for 5 minutes (rollback window)

### 2. Canary Deployment

Not natively supported. Use feature flags or Railway's PR environments:

```bash
# Deploy to PR environment
railway up --environment pr-123

# Test with subset of traffic
# If successful, merge to main
```

### 3. Rollback

```bash
# List deployments
railway deployments

# Rollback to previous deployment
railway rollback <deployment-id>
```

## Security Best Practices

### 1. Environment Variables

- Never commit secrets to Git
- Use Railway's environment variables
- Rotate secrets regularly (90 days)

### 2. Network Security

- Enable Railway's private networking
- Use Railway's built-in firewall
- Restrict database access to internal services

### 3. SSL/TLS

- Railway provides automatic SSL/TLS
- Enforce HTTPS redirects
- Use TLS 1.3

### 4. Access Control

- Use Railway's team access controls
- Enable 2FA for all team members
- Regular access audits

## Troubleshooting

### Service Won't Start

```bash
# Check logs
railway logs --service backend --tail 100

# Check environment variables
railway variables --service backend

# Restart service
railway restart --service backend
```

### High Memory Usage

```bash
# Check metrics
railway metrics --service backend

# Increase memory limit
railway scale backend --memory 4096

# Profile application
railway run --service backend python -m memory_profiler src/api/main.py
```

### Database Connection Issues

```bash
# Test database connection
railway run --service backend python -c "from config.settings import get_settings; print(get_settings().database)"

# Check connection pool
railway run --service backend psql -c "SELECT count(*) FROM pg_stat_activity;"
```

### Slow Deployment

```bash
# Use multi-stage Docker builds (already configured)
# Enable BuildKit caching
export DOCKER_BUILDKIT=1

# Pre-build images locally
docker build -f docker/Dockerfile.backend -t backend .
docker push your-registry/backend
```

## Cost Optimization

### 1. Right-Size Resources

Monitor actual usage:

```bash
railway metrics --service backend --period 7d
```

Adjust resources based on peak usage + 20% buffer.

### 2. Scale Down Off-Hours

For non-production environments:

```bash
# Scale down at night (requires cron job)
railway scale backend --replicas 1

# Scale up in morning
railway scale backend --replicas 2
```

### 3. Optimize Docker Images

- Use multi-stage builds (already configured)
- Minimize layers
- Use .dockerignore

### 4. Database Query Optimization

- Enable pg_stat_statements
- Analyze slow queries
- Add appropriate indexes

## Maintenance Windows

### Planned Maintenance

1. Announce maintenance 7 days in advance
2. Schedule during low-traffic hours
3. Use blue-green deployment for zero downtime
4. Keep rollback plan ready

### Emergency Maintenance

1. Alert on-call team
2. Enable maintenance mode
3. Fix critical issue
4. Verify with health checks
5. Restore service
6. Post-mortem analysis

## Production Checklist

- [ ] All environment variables configured
- [ ] Database migrations run successfully
- [ ] Health checks passing
- [ ] SSL/TLS certificates provisioned
- [ ] Custom domains configured
- [ ] Monitoring and alerts set up
- [ ] Backup strategy verified
- [ ] Load testing completed
- [ ] Security audit passed
- [ ] Documentation updated
- [ ] Team trained on Railway operations
- [ ] Rollback plan tested
- [ ] Disaster recovery plan documented

## Support Resources

- Railway Documentation: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Railway Status: https://status.railway.app
- Internal Documentation: ./docs/infrastructure/

## Emergency Contacts

- On-Call Engineer: [phone]
- DevOps Lead: [phone]
- Railway Support: support@railway.app
- Database Admin: [phone]
