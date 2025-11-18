# Operations Runbook

## Overview

This runbook provides step-by-step procedures for common operational tasks, incident response, and system maintenance for the SEC Filing Analysis System.

## Daily Operations

### Morning Health Check

**Frequency**: Every weekday at 9:00 AM

**Procedure**:
```bash
# 1. Check system health
curl https://api.sec-analysis.com/health

# 2. Check Grafana dashboards
open https://grafana.sec-analysis.com/dashboards

# 3. Review overnight processing
kubectl logs -l app=celery-worker --since=24h | grep ERROR

# 4. Check task queue depth
redis-cli -h redis.sec-analysis.com LLEN celery

# 5. Verify database connections
kubectl exec -it deployment/api -- psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity"
```

**Expected Results**:
- Health endpoint returns 200 OK
- All services show "healthy" status
- Error rate < 1%
- Task queue depth < 100
- Active database connections < 80% of max

**Escalation**: If any metric is out of range, follow [Incident Response](#incident-response) procedures.

### Weekly Maintenance

**Frequency**: Every Sunday at 2:00 AM

**Tasks**:
1. Database backup verification
2. Log rotation and archival
3. Certificate renewal check
4. Dependency security scan
5. Performance metrics review

**Procedure**:
```bash
# 1. Verify backups
aws s3 ls s3://backups/sec-analysis/ --recursive | tail -7

# 2. Rotate logs
kubectl delete pods -l app=api --force --grace-period=0
kubectl delete pods -l app=celery-worker --force --grace-period=0

# 3. Check certificates
kubectl get certificates -n sec-analysis

# 4. Security scan
trivy image your-registry/sec-analysis-api:latest

# 5. Review performance
# Access Grafana and review weekly summary dashboard
```

## Incident Response

### Severity Levels

**P0 - Critical**:
- System completely down
- Data loss or corruption
- Security breach
- Response time: Immediate
- Escalation: All hands on deck

**P1 - High**:
- Major functionality unavailable
- Significant performance degradation
- Response time: < 15 minutes
- Escalation: On-call engineer + manager

**P2 - Medium**:
- Partial functionality affected
- Minor performance issues
- Response time: < 1 hour
- Escalation: On-call engineer

**P3 - Low**:
- Cosmetic issues
- Feature requests
- Response time: Next business day
- Escalation: Ticket queue

### Incident Response Workflow

```
Incident Detected
      ↓
  Assess Severity
      ↓
Create Incident Ticket
      ↓
  Notify Team
      ↓
  Initial Response
      ↓
  Root Cause Analysis
      ↓
  Apply Fix
      ↓
  Verify Resolution
      ↓
Post-Mortem Report
```

### P0: System Down

**Symptoms**:
- Health endpoint returns 500 error
- All API requests failing
- No task processing

**Immediate Actions**:
```bash
# 1. Create incident channel
# Slack: #incident-<timestamp>

# 2. Check infrastructure
kubectl get pods -n sec-analysis
kubectl get nodes

# 3. Check database
kubectl exec -it deployment/api -- psql $DATABASE_URL -c "SELECT 1"

# 4. Check Redis
redis-cli -h redis.sec-analysis.com PING

# 5. Review recent deployments
kubectl rollout history deployment/api -n sec-analysis
```

**Recovery Steps**:

Option A - Rollback:
```bash
kubectl rollout undo deployment/api -n sec-analysis
kubectl rollout status deployment/api -n sec-analysis
```

Option B - Scale up:
```bash
kubectl scale deployment/api --replicas=10 -n sec-analysis
```

Option C - Restart services:
```bash
kubectl delete pods -l app=api
kubectl delete pods -l app=celery-worker
```

Option D - Database failover:
```bash
# Supabase automatic failover
# Monitor via dashboard: https://app.supabase.com/project/_/settings/infrastructure
```

**Verification**:
```bash
# Check health
curl https://api.sec-analysis.com/health

# Run end-to-end test
curl -X POST https://api.sec-analysis.com/filings/process \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"cik": "0000789019", "form_type": "10-Q"}'
```

### P1: Database Performance Degradation

**Symptoms**:
- Slow query responses (>5 seconds)
- Increased database CPU usage (>80%)
- Connection pool exhaustion

**Diagnosis**:
```sql
-- Check slow queries
SELECT pid, query, state, wait_event_type, wait_event
FROM pg_stat_activity
WHERE state != 'idle'
AND query_start < now() - interval '5 seconds'
ORDER BY query_start;

-- Check connection pool
SELECT count(*) as connections, state
FROM pg_stat_activity
GROUP BY state;

-- Check table bloat
SELECT schemaname, tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;
```

**Resolution**:

Option A - Kill slow queries:
```sql
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'active'
AND query_start < now() - interval '1 minute';
```

Option B - Scale database:
```bash
# Increase Supabase compute
# Via dashboard: Settings → Infrastructure → Compute Add-ons
```

Option C - Add indexes:
```sql
CREATE INDEX CONCURRENTLY idx_filings_cik_date
ON filings(cik, filing_date DESC);

CREATE INDEX CONCURRENTLY idx_signals_filing_category
ON signals(filing_id, category);
```

Option D - Vacuum database:
```sql
VACUUM ANALYZE filings;
VACUUM ANALYZE signals;
```

### P1: High Task Queue Depth

**Symptoms**:
- Task queue depth > 1000
- Tasks not processing
- Increased API latency

**Diagnosis**:
```bash
# Check queue depth
redis-cli -h redis.sec-analysis.com LLEN celery

# Check active workers
kubectl get pods -l app=celery-worker

# Check worker logs
kubectl logs -l app=celery-worker --tail=100
```

**Resolution**:

Option A - Scale workers:
```bash
kubectl scale deployment/celery-worker --replicas=20 -n sec-analysis
```

Option B - Purge old tasks:
```bash
# Purge tasks older than 24 hours
celery -A src.pipeline.celery_tasks purge

# Or use CLI
kubectl exec -it deployment/celery-worker -- \
  celery -A src.pipeline.celery_tasks purge
```

Option C - Restart workers:
```bash
kubectl delete pods -l app=celery-worker
```

Option D - Adjust concurrency:
```bash
# Update worker concurrency
kubectl set env deployment/celery-worker CELERY_WORKER_CONCURRENCY=8
```

### P2: Model Inference Timeout

**Symptoms**:
- Model inference exceeds 30 seconds
- Increased task failures
- GPU memory errors

**Diagnosis**:
```bash
# Check GPU utilization
kubectl exec -it <worker-pod> -- nvidia-smi

# Check model cache
kubectl exec -it <worker-pod> -- ls -lh /models/cache

# Check worker memory
kubectl top pods -l app=celery-worker
```

**Resolution**:

Option A - Restart workers with GPU:
```bash
kubectl delete pods -l app=celery-worker,gpu=true
```

Option B - Clear model cache:
```bash
kubectl exec -it <worker-pod> -- rm -rf /models/cache/*
```

Option C - Route to faster model:
```bash
# Temporarily lower complexity threshold
kubectl set env deployment/api COMPLEXITY_THRESHOLD_HIGH=0.9
```

Option D - Scale GPU workers:
```bash
kubectl scale deployment/celery-worker-gpu --replicas=5
```

## Maintenance Procedures

### Database Maintenance

**Monthly Vacuum**:
```sql
-- Full vacuum (requires maintenance window)
VACUUM FULL ANALYZE;

-- Or online vacuum
VACUUM ANALYZE filings;
VACUUM ANALYZE signals;
VACUUM ANALYZE validations;
```

**Index Rebuild**:
```sql
-- Concurrent rebuild (no downtime)
REINDEX INDEX CONCURRENTLY idx_filings_cik_date;

-- Full reindex (requires maintenance window)
REINDEX TABLE filings;
```

**Statistics Update**:
```sql
ANALYZE filings;
ANALYZE signals;
```

### Redis Maintenance

**Memory Optimization**:
```bash
# Check memory usage
redis-cli -h redis.sec-analysis.com INFO memory

# Clear expired keys
redis-cli -h redis.sec-analysis.com --scan --pattern "celery*" | xargs redis-cli DEL

# Optimize memory
redis-cli -h redis.sec-analysis.com CONFIG SET maxmemory-policy allkeys-lru
```

### Certificate Renewal

**Check Expiration**:
```bash
kubectl get certificates -n sec-analysis
kubectl describe certificate api-tls -n sec-analysis
```

**Manual Renewal** (if needed):
```bash
kubectl delete certificate api-tls -n sec-analysis
kubectl apply -f k8s/certificates.yaml
```

### Log Management

**Archive Old Logs**:
```bash
# Archive logs older than 90 days
kubectl logs -l app=api --since=2160h > logs/api-$(date +%Y%m%d).log
gzip logs/api-$(date +%Y%m%d).log
aws s3 cp logs/api-$(date +%Y%m%d).log.gz s3://logs-archive/

# Rotate Elasticsearch indices
curator delete indices --older-than 90 --time-unit days
```

## Monitoring & Alerting

### Key Metrics to Monitor

**System Health**:
- API response time (P95 < 1s)
- Error rate (< 1%)
- Task queue depth (< 100)
- Worker utilization (< 80%)

**Database**:
- Connection pool usage (< 80%)
- Query latency (P95 < 500ms)
- Replication lag (< 1s)
- Disk usage (< 80%)

**Application**:
- Signal extraction accuracy (> 95%)
- Validation pass rate (> 90%)
- Model inference time (P95 < 30s)
- Cost per filing (< $0.50)

### Alert Thresholds

**Critical Alerts**:
```yaml
- name: APIDown
  condition: health_check_status != 200
  duration: 2m
  severity: P0

- name: DatabaseDown
  condition: db_connection_count == 0
  duration: 1m
  severity: P0

- name: HighErrorRate
  condition: error_rate > 5%
  duration: 5m
  severity: P0
```

**Warning Alerts**:
```yaml
- name: HighLatency
  condition: p95_latency > 2s
  duration: 10m
  severity: P1

- name: LowDiskSpace
  condition: disk_usage > 80%
  duration: 30m
  severity: P1

- name: HighQueueDepth
  condition: queue_depth > 500
  duration: 15m
  severity: P1
```

## Backup & Recovery

### Backup Schedule

**Daily Backups**:
- Database: 2:00 AM UTC
- Configuration: 3:00 AM UTC
- Retention: 30 days

**Weekly Backups**:
- Full system snapshot: Sunday 1:00 AM UTC
- Retention: 90 days

### Recovery Procedures

**Restore Database**:
```bash
# 1. Download backup
aws s3 cp s3://backups/sec-analysis/db_20250218_020000.sql.gz .
gunzip db_20250218_020000.sql.gz

# 2. Create maintenance window
kubectl scale deployment/api --replicas=0
kubectl scale deployment/celery-worker --replicas=0

# 3. Restore database
psql $DATABASE_URL < db_20250218_020000.sql

# 4. Verify data
psql $DATABASE_URL -c "SELECT count(*) FROM filings"

# 5. Resume services
kubectl scale deployment/api --replicas=3
kubectl scale deployment/celery-worker --replicas=5
```

**Point-in-Time Recovery**:
```bash
# Via Supabase dashboard
# Settings → Database → Point in Time Recovery
# Select timestamp and restore
```

## Security Operations

### Security Incident Response

**Suspected Breach**:
```bash
# 1. Rotate all secrets immediately
kubectl delete secret sec-analysis-secrets
kubectl create secret generic sec-analysis-secrets --from-env-file=.env.secure

# 2. Audit access logs
kubectl logs -l app=api | grep "401\|403"

# 3. Check for unauthorized pods
kubectl get pods --all-namespaces | grep -v "sec-analysis\|kube-system"

# 4. Review database access
SELECT * FROM pg_stat_activity
WHERE usename NOT IN ('service_account', 'readonly_user');
```

**API Key Compromise**:
```bash
# 1. Revoke compromised key
curl -X DELETE https://api.sec-analysis.com/auth/keys/$KEY_ID

# 2. Generate new key
curl -X POST https://api.sec-analysis.com/auth/keys

# 3. Update clients
# Coordinate with API consumers to update keys

# 4. Audit API usage
# Check for abnormal patterns with compromised key
```

### Access Control Review

**Monthly Access Audit**:
```bash
# Review Kubernetes RBAC
kubectl get rolebindings -n sec-analysis
kubectl get clusterrolebindings

# Review database users
psql $DATABASE_URL -c "\du"

# Review API keys
curl https://api.sec-analysis.com/admin/keys \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

## Performance Optimization

### Database Optimization

**Query Performance**:
```sql
-- Find slow queries
SELECT mean_exec_time, calls, query
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Add missing indexes
SELECT schemaname, tablename, attname
FROM pg_stats
WHERE null_frac > 0.5
AND n_distinct > 100;
```

**Connection Pooling**:
```bash
# Optimize PgBouncer settings
kubectl edit configmap pgbouncer-config

# pool_mode = transaction
# max_client_conn = 1000
# default_pool_size = 25
```

### Application Optimization

**Cache Hit Rate**:
```bash
# Check Redis cache hit rate
redis-cli -h redis.sec-analysis.com INFO stats | grep hit

# Adjust TTL for hot data
redis-cli -h redis.sec-analysis.com CONFIG SET maxmemory 8gb
```

**Worker Optimization**:
```bash
# Adjust worker concurrency based on load
kubectl set env deployment/celery-worker \
  CELERY_WORKER_CONCURRENCY=6 \
  CELERY_PREFETCH_MULTIPLIER=2
```

## On-Call Procedures

### On-Call Rotation

**Schedule**:
- Primary: 1 week rotation
- Secondary: 1 week rotation
- Handoff: Monday 9:00 AM

**Handoff Checklist**:
- Review open incidents
- Check system health
- Review upcoming maintenance
- Test pager/alerts
- Update on-call contact info

### Escalation Paths

**P0 Incidents**:
1. On-call engineer (immediate)
2. Engineering manager (if no response in 15 min)
3. CTO (if no response in 30 min)

**P1 Incidents**:
1. On-call engineer (< 15 min)
2. Engineering manager (if no resolution in 1 hour)

### Contact Information

```
On-Call Engineer: pagerduty.com/sec-analysis
Engineering Manager: manager@company.com
DevOps Lead: devops@company.com
Security Team: security@company.com
Emergency Hotline: +1-555-HELP-NOW
```

---

**Document Version**: 1.0
**Last Updated**: 2025-10-18
**Owner**: Operations Team
**Review Cycle**: Monthly
