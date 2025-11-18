# Disaster Recovery Runbook

## Overview
This runbook provides step-by-step procedures for recovering from various disaster scenarios.

**Recovery Time Objective (RTO):** 4 hours
**Recovery Point Objective (RPO):** 1 hour

## Disaster Scenarios

### 1. Complete Database Failure

#### Detection
- Multiple database connection failures
- Alert: PostgreSQLDown firing
- Health endpoint shows database unhealthy

#### Recovery Steps

```bash
# 1. Assess the situation
kubectl logs deployment/sec-latent-backend -n production | grep -i "database"

# 2. Check database pod status
kubectl get pods -n production -l app=postgres

# 3. Attempt pod restart
kubectl rollout restart deployment/postgres -n production

# 4. If restart fails, restore from backup
./scripts/backup/restore-database.sh production /backups/postgres/production/backup_daily_YYYYMMDD_HHMMSS.sql.gz

# 5. Verify restoration
psql -h postgres -U secuser -d sec_latent -c "SELECT COUNT(*) FROM filings;"

# 6. Restart application services
kubectl rollout restart deployment/sec-latent-backend -n production
kubectl rollout restart deployment/sec-latent-worker -n production

# 7. Run smoke tests
./scripts/health-checks/smoke-test.sh https://sec-latent.example.com
```

**Estimated Recovery Time:** 2-3 hours

### 2. Application Deployment Failure

#### Detection
- High error rates after deployment
- Failed health checks
- Alert: HighErrorRate firing

#### Recovery Steps

```bash
# 1. Immediate rollback to previous version
kubectl rollout undo deployment/sec-latent-backend -n production
kubectl rollout undo deployment/sec-latent-frontend -n production
kubectl rollout undo deployment/sec-latent-worker -n production

# 2. Verify rollback status
kubectl rollout status deployment/sec-latent-backend -n production

# 3. Switch traffic back to blue environment
kubectl patch service sec-latent-backend -n production -p '{"spec":{"selector":{"version":"blue"}}}'
kubectl patch service sec-latent-frontend -n production -p '{"spec":{"selector":{"version":"blue"}}}'

# 4. Scale blue environment
kubectl scale deployment/sec-latent-backend-blue -n production --replicas=3
kubectl scale deployment/sec-latent-frontend-blue -n production --replicas=2

# 5. Run verification
./scripts/health-checks/smoke-test.sh https://sec-latent.example.com

# 6. Investigate failure
kubectl logs deployment/sec-latent-backend-green -n production --tail=1000 > deployment-failure.log
```

**Estimated Recovery Time:** 15-30 minutes

### 3. Redis Cache Failure

#### Detection
- Redis connection errors
- Cache miss rate approaching 100%
- Alert: RedisDown firing

#### Recovery Steps

```bash
# 1. Restart Redis pod
kubectl rollout restart deployment/redis -n production

# 2. Check Redis data persistence
kubectl exec -it deployment/redis -n production -- redis-cli INFO persistence

# 3. If data lost, clear cache and warm up
kubectl exec -it deployment/redis -n production -- redis-cli FLUSHALL

# 4. Trigger cache warming
curl -X POST https://sec-latent.example.com/api/v1/admin/cache/warm

# 5. Monitor cache hit rate
watch -n 5 'kubectl exec deployment/redis -n production -- redis-cli INFO stats | grep keyspace'
```

**Estimated Recovery Time:** 30 minutes - 1 hour

### 4. Complete Infrastructure Failure

#### Detection
- All services down
- No response from any endpoint
- Multiple critical alerts firing

#### Recovery Steps

```bash
# 1. Assess infrastructure status
kubectl get nodes
kubectl get pods --all-namespaces

# 2. If Kubernetes cluster down, restore from infrastructure-as-code
terraform apply -auto-approve

# 3. Restore database from latest backup
./scripts/backup/restore-database.sh production s3://sec-latent-backups/production/daily/latest.sql.gz

# 4. Deploy application from scratch
kubectl apply -k k8s/overlays/prod/

# 5. Wait for deployments to be ready
kubectl wait --for=condition=available --timeout=600s deployment --all -n production

# 6. Verify all services
./scripts/health-checks/smoke-test.sh https://sec-latent.example.com

# 7. Monitor for 30 minutes
./scripts/health-checks/monitor-deployment.sh production 1800
```

**Estimated Recovery Time:** 3-4 hours

## Backup Verification

### Daily Verification Tasks
```bash
# 1. Verify backup exists
ls -lh /backups/postgres/production/ | tail -5

# 2. Test backup integrity
gunzip -t /backups/postgres/production/backup_daily_$(date +%Y%m%d)_*.sql.gz

# 3. Verify S3 upload
aws s3 ls s3://sec-latent-backups/production/daily/ | tail -5

# 4. Verify backup metadata
cat /backups/postgres/production/backup_daily_$(date +%Y%m%d)_*.meta
```

### Weekly Restoration Test
```bash
# 1. Create test database
psql -h postgres-test -U secuser -c "CREATE DATABASE sec_latent_restore_test;"

# 2. Restore latest backup
gunzip -c /backups/postgres/production/backup_daily_latest.sql.gz | \
  psql -h postgres-test -U secuser -d sec_latent_restore_test

# 3. Verify data integrity
psql -h postgres-test -U secuser -d sec_latent_restore_test -c "
  SELECT
    (SELECT COUNT(*) FROM filings) as filing_count,
    (SELECT COUNT(*) FROM predictions) as prediction_count,
    (SELECT MAX(created_at) FROM filings) as latest_filing;
"

# 4. Cleanup
psql -h postgres-test -U secuser -c "DROP DATABASE sec_latent_restore_test;"
```

## Contact Information

### On-Call Rotation
- **Primary:** DevOps Team (+1-XXX-XXX-XXXX)
- **Secondary:** Backend Team (+1-XXX-XXX-XXXX)
- **Escalation:** CTO (+1-XXX-XXX-XXXX)

### External Vendors
- **AWS Support:** +1-XXX-XXX-XXXX
- **Database Consultant:** consultant@example.com
- **Security Team:** security@example.com

## Post-Incident Procedures

1. **Document incident** in post-mortem template
2. **Update runbook** with lessons learned
3. **Schedule retrospective** within 48 hours
4. **Implement improvements** to prevent recurrence
5. **Test disaster recovery** plan quarterly
