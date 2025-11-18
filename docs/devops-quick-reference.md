# DevOps Quick Reference Guide

## Common Operations

### Deployments

#### Deploy to Staging
```bash
git push origin staging
# CI/CD automatically deploys after tests pass
```

#### Deploy to Production
```bash
git push origin main
# Blue-green deployment with automatic health checks
```

#### Manual Rollback
```bash
./scripts/rollback/rollback-deployment.sh production "reason"
```

### Backups

#### Create Manual Backup
```bash
./scripts/backup/backup-database.sh production daily
```

#### Restore from Backup
```bash
./scripts/backup/restore-database.sh production /path/to/backup.sql.gz
```

#### List Available Backups
```bash
ls -lh /backups/postgres/production/
aws s3 ls s3://sec-latent-backups/production/daily/
```

### Monitoring

#### Check Application Health
```bash
curl https://sec-latent.example.com/health | jq
```

#### View Grafana Dashboards
- Infrastructure: https://grafana.sec-latent.example.com/d/infrastructure
- Application: https://grafana.sec-latent.example.com/d/application

#### Check Prometheus Alerts
```bash
kubectl port-forward svc/prometheus 9090:9090 -n monitoring
# Open http://localhost:9090/alerts
```

#### View Application Logs
```bash
kubectl logs deployment/sec-latent-backend -n production --tail=100 -f
```

#### Search Logs in Kibana
https://kibana.sec-latent.example.com

### Health Checks

#### Run Smoke Tests
```bash
./scripts/health-checks/smoke-test.sh https://sec-latent.example.com
```

#### Monitor Deployment
```bash
./scripts/health-checks/monitor-deployment.sh production 300
```

### Kubernetes Operations

#### Check Pod Status
```bash
kubectl get pods -n production
kubectl describe pod <pod-name> -n production
```

#### Scale Deployment
```bash
kubectl scale deployment/sec-latent-backend -n production --replicas=5
```

#### Restart Deployment
```bash
kubectl rollout restart deployment/sec-latent-backend -n production
```

#### View Deployment History
```bash
kubectl rollout history deployment/sec-latent-backend -n production
```

## Troubleshooting

### High Error Rate

1. Check application logs:
```bash
kubectl logs deployment/sec-latent-backend -n production | grep ERROR
```

2. Check Sentry for error details:
https://sentry.io/organizations/sec-latent/issues/

3. If persistent, rollback:
```bash
./scripts/rollback/rollback-deployment.sh production "High error rate"
```

### Database Connection Issues

1. Check database pod:
```bash
kubectl get pods -n production -l app=postgres
kubectl logs deployment/postgres -n production
```

2. Check connection pool:
```bash
curl https://sec-latent.example.com/health | jq '.services.database'
```

3. Restart database if needed:
```bash
kubectl rollout restart deployment/postgres -n production
```

### Redis Cache Issues

1. Check Redis status:
```bash
kubectl exec deployment/redis -n production -- redis-cli INFO
```

2. Clear cache if needed:
```bash
kubectl exec deployment/redis -n production -- redis-cli FLUSHALL
```

### Slow Response Times

1. Check Grafana for bottlenecks
2. Review database query performance:
```bash
kubectl exec deployment/postgres -n production -- \
  psql -U secuser -d sec_latent -c "
    SELECT query, mean_exec_time, calls
    FROM pg_stat_statements
    ORDER BY mean_exec_time DESC
    LIMIT 10;"
```

## Alerts and Notifications

### Slack Channels
- `#alerts-production` - Production alerts
- `#alerts-staging` - Staging alerts
- `#deployments` - Deployment notifications

### On-Call Escalation
1. Check alert in AlertManager
2. Review runbook: `/docs/disaster-recovery-runbook.md`
3. Contact on-call engineer
4. Escalate to CTO if critical

## Environment Variables

### Required Secrets
```bash
POSTGRES_PASSWORD
REDIS_PASSWORD
SENTRY_DSN
SENTRY_AUTH_TOKEN
S3_BACKUP_BUCKET
SLACK_WEBHOOK
```

### Optional Configuration
```bash
ENVIRONMENT=production
LOG_LEVEL=INFO
CELERY_WORKER_CONCURRENCY=4
SEC_RATE_LIMIT=10
```

## CI/CD Pipeline

### Workflow Triggers
- **Push to main:** Production deployment
- **Push to staging:** Staging deployment
- **Pull request:** Tests only
- **Nightly:** Security scans

### Pipeline Stages
1. Security scanning (2-3 minutes)
2. Backend tests (5-7 minutes)
3. Frontend tests (3-5 minutes)
4. Docker image building (10-15 minutes)
5. Deployment (5-10 minutes)
6. Smoke tests (2-3 minutes)

**Total Time:** ~30-45 minutes

## Performance Baselines

### Expected Metrics
- API Response Time (p95): < 500ms
- API Response Time (p99): < 2s
- Error Rate: < 0.1%
- Database Connections: < 80% of max
- Redis Memory Usage: < 80%
- CPU Usage: < 70% average
- Memory Usage: < 80%

### Alert Thresholds
- Error Rate > 5% for 5 minutes
- Response Time (p95) > 2s for 10 minutes
- Database Connections > 80% for 5 minutes
- High CPU/Memory > 80% for 10 minutes

## Useful Commands

### Kubernetes
```bash
# Get all resources in namespace
kubectl get all -n production

# Get events
kubectl get events -n production --sort-by='.lastTimestamp'

# Execute command in pod
kubectl exec -it deployment/sec-latent-backend -n production -- bash

# Port forward for local debugging
kubectl port-forward deployment/sec-latent-backend 8000:8000 -n production
```

### Docker
```bash
# View running containers
docker ps

# View logs
docker logs sec-latent-backend --tail=100 -f

# Execute command in container
docker exec -it sec-latent-backend bash
```

### Database
```bash
# Connect to database
kubectl exec -it deployment/postgres -n production -- \
  psql -U secuser -d sec_latent

# Database size
SELECT pg_size_pretty(pg_database_size('sec_latent'));

# Active connections
SELECT count(*) FROM pg_stat_activity;

# Slow queries
SELECT query, mean_exec_time
FROM pg_stat_statements
WHERE mean_exec_time > 1000
ORDER BY mean_exec_time DESC;
```

### Redis
```bash
# Connect to Redis
kubectl exec -it deployment/redis -n production -- redis-cli

# Check memory
INFO memory

# Check keyspace
INFO keyspace

# Monitor commands
MONITOR
```

## Security

### Access Control
- **Production:** Requires approval from 2 team members
- **Staging:** All developers have access
- **Secrets:** Managed via Kubernetes secrets

### Audit Logging
- All kubectl commands logged
- Database access logged
- API access logged in application logs

### Incident Response
1. Identify issue severity
2. Follow runbook procedures
3. Document in incident report
4. Post-mortem within 48 hours

## Support Contacts

- **DevOps Lead:** devops-lead@example.com
- **Backend Lead:** backend-lead@example.com
- **Security Team:** security@example.com
- **On-Call:** Use PagerDuty rotation

---

**Last Updated:** 2025-10-19
**Maintained By:** DevOps Team
