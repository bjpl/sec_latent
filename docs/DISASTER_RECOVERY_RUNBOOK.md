# SEC Latent - Disaster Recovery Runbook

## Table of Contents
1. [Emergency Contacts](#emergency-contacts)
2. [Recovery Time Objectives](#recovery-time-objectives)
3. [Incident Response Procedures](#incident-response-procedures)
4. [Database Recovery](#database-recovery)
5. [Application Recovery](#application-recovery)
6. [Data Corruption Scenarios](#data-corruption-scenarios)
7. [Complete System Failure](#complete-system-failure)
8. [Post-Recovery Validation](#post-recovery-validation)

## Emergency Contacts

| Role | Contact | Phone | Email |
|------|---------|-------|-------|
| On-Call Engineer | Primary | xxx-xxx-xxxx | oncall@example.com |
| Database Admin | DBA Team | xxx-xxx-xxxx | dba@example.com |
| Infrastructure Lead | Infra Team | xxx-xxx-xxxx | infra@example.com |
| Security Team | Security | xxx-xxx-xxxx | security@example.com |
| Management | CTO | xxx-xxx-xxxx | cto@example.com |

## Recovery Time Objectives (RTO/RPO)

| Component | RTO | RPO | Priority |
|-----------|-----|-----|----------|
| PostgreSQL Database | 15 min | 5 min | Critical |
| Backend API | 10 min | N/A | Critical |
| Frontend | 5 min | N/A | High |
| Celery Workers | 15 min | N/A | High |
| Redis Cache | 5 min | 1 hour | Medium |
| ELK Stack | 30 min | 24 hours | Low |

## Incident Response Procedures

### 1. Initial Assessment (0-5 minutes)

```bash
# Check system health
kubectl get pods -n sec-latent
kubectl get nodes
kubectl top nodes

# Check recent events
kubectl get events -n sec-latent --sort-by='.lastTimestamp'

# Check logs
kubectl logs -n sec-latent -l app=sec-latent --tail=100

# Check monitoring dashboards
# Open: https://grafana.example.com/d/sec-latent-overview
```

### 2. Incident Classification

- **Severity 1 (Critical)**: Complete system down, data loss
- **Severity 2 (High)**: Major functionality impaired, no data loss
- **Severity 3 (Medium)**: Partial functionality impaired
- **Severity 4 (Low)**: Minor issues, workarounds available

### 3. Escalation Procedure

1. **Sev 1**: Immediately page on-call engineer and management
2. **Sev 2**: Page on-call engineer within 15 minutes
3. **Sev 3**: Create ticket, assign to on-call
4. **Sev 4**: Create ticket, handle during business hours

## Database Recovery

### PostgreSQL Complete Failure

**Scenario**: PostgreSQL pod crashes or database corruption

**Detection**:
```bash
kubectl logs -n sec-latent sec-latent-postgres-0 --tail=100
```

**Recovery Steps**:

1. **Verify Backups Available**
```bash
cd /var/backups/sec-latent
ls -lh $(date +%Y-%m-%d)/postgres_*.sql*
```

2. **Stop Application Traffic**
```bash
kubectl scale deployment sec-latent-backend -n sec-latent --replicas=0
kubectl scale deployment sec-latent-worker -n sec-latent --replicas=0
```

3. **Restore Database**
```bash
# Find latest backup
LATEST_BACKUP=$(ls -t /var/backups/sec-latent/*/postgres_production_*.sql | head -1)

# Verify checksum
sha256sum -c "${LATEST_BACKUP}.sha256"

# Decrypt if necessary
if [[ "$LATEST_BACKUP" == *.enc ]]; then
    openssl enc -aes-256-cbc -d \
        -in "$LATEST_BACKUP" \
        -out "${LATEST_BACKUP%.enc}" \
        -pass pass:"$ENCRYPTION_KEY"
    LATEST_BACKUP="${LATEST_BACKUP%.enc}"
fi

# Restore database
kubectl exec -n sec-latent sec-latent-postgres-0 -- \
    pg_restore \
    -U secuser \
    -d sec_latent \
    --clean \
    --if-exists \
    --verbose \
    < "$LATEST_BACKUP"
```

4. **Verify Database Integrity**
```bash
kubectl exec -n sec-latent sec-latent-postgres-0 -- \
    psql -U secuser -d sec_latent -c "
    SELECT COUNT(*) FROM pg_stat_user_tables;
    SELECT schemaname, tablename, n_live_tup
    FROM pg_stat_user_tables
    ORDER BY n_live_tup DESC
    LIMIT 10;
    "
```

5. **Restore Application Traffic**
```bash
kubectl scale deployment sec-latent-backend -n sec-latent --replicas=3
kubectl scale deployment sec-latent-worker -n sec-latent --replicas=2
```

6. **Monitor Recovery**
```bash
watch -n 5 'kubectl get pods -n sec-latent'
```

**Expected Recovery Time**: 15-20 minutes
**Data Loss**: Up to 5 minutes (last backup interval)

### Redis Cache Failure

**Scenario**: Redis pod crashes or data loss

**Detection**:
```bash
kubectl logs -n sec-latent sec-latent-redis-0 --tail=100
```

**Recovery Steps**:

1. **Redis is Cache-Only** - Application should continue with degraded performance
2. **Restart Redis Pod**
```bash
kubectl delete pod -n sec-latent sec-latent-redis-0
```

3. **Verify Pod Restarted**
```bash
kubectl get pod -n sec-latent -l app=redis
```

4. **Cache Will Warm Up Naturally** - No immediate action needed

**Expected Recovery Time**: 2-3 minutes
**Data Loss**: Acceptable (cache only)

## Application Recovery

### Backend API Crash Loop

**Scenario**: Backend pods in CrashLoopBackOff

**Detection**:
```bash
kubectl get pods -n sec-latent -l component=backend
kubectl describe pod -n sec-latent <pod-name>
kubectl logs -n sec-latent <pod-name> --previous
```

**Common Causes**:
- Configuration error
- Database connection failure
- Memory/CPU limits exceeded
- Dependency service unavailable

**Recovery Steps**:

1. **Check Configuration**
```bash
kubectl get configmap -n sec-latent sec-latent-config -o yaml
kubectl get secret -n sec-latent sec-latent-secrets -o yaml
```

2. **Verify Dependencies**
```bash
kubectl get pods -n sec-latent -l component=database
kubectl get pods -n sec-latent -l component=cache
```

3. **Check Resources**
```bash
kubectl top pods -n sec-latent
kubectl describe node <node-name>
```

4. **Rollback if Recent Deployment**
```bash
kubectl rollout history deployment/sec-latent-backend -n sec-latent
kubectl rollout undo deployment/sec-latent-backend -n sec-latent
```

5. **Force Restart**
```bash
kubectl rollout restart deployment/sec-latent-backend -n sec-latent
```

**Expected Recovery Time**: 5-10 minutes

### Frontend Serving Errors

**Scenario**: Frontend returns 5xx errors or blank pages

**Detection**:
```bash
kubectl logs -n sec-latent -l component=frontend --tail=100
curl -I https://sec-latent.example.com
```

**Recovery Steps**:

1. **Check Backend Connectivity**
```bash
kubectl exec -n sec-latent <frontend-pod> -- \
    curl -I http://sec-latent-backend:8000/health
```

2. **Check Ingress Configuration**
```bash
kubectl get ingress -n sec-latent sec-latent-ingress -o yaml
```

3. **Restart Frontend Pods**
```bash
kubectl rollout restart deployment/sec-latent-frontend -n sec-latent
```

**Expected Recovery Time**: 3-5 minutes

### Celery Worker Queue Backup

**Scenario**: Tasks queuing without processing

**Detection**:
```bash
# Check queue length (should be in Flower or metrics)
kubectl exec -n sec-latent sec-latent-redis-0 -- \
    redis-cli -a "$REDIS_PASSWORD" llen celery

kubectl logs -n sec-latent -l component=worker --tail=50
```

**Recovery Steps**:

1. **Scale Up Workers**
```bash
kubectl scale deployment/sec-latent-worker -n sec-latent --replicas=10
```

2. **Check for Stuck Tasks**
```bash
# Access Flower dashboard
kubectl port-forward -n sec-latent svc/sec-latent-flower 5555:5555
# Open http://localhost:5555
```

3. **Purge Failed Tasks if Necessary**
```bash
kubectl exec -n sec-latent sec-latent-worker-0 -- \
    celery -A src.pipeline.celery_tasks purge
```

**Expected Recovery Time**: 10-30 minutes (depends on queue size)

## Data Corruption Scenarios

### Detected Data Corruption

**Scenario**: Data integrity violations detected

**Detection**:
- Sentry alerts
- Data validation failures
- User reports

**Recovery Steps**:

1. **Immediate Actions**
```bash
# Stop all write operations
kubectl scale deployment sec-latent-backend -n sec-latent --replicas=0
kubectl scale deployment sec-latent-worker -n sec-latent --replicas=0
```

2. **Assess Corruption Extent**
```bash
# Run data integrity checks
kubectl exec -n sec-latent sec-latent-postgres-0 -- \
    psql -U secuser -d sec_latent -f /app/scripts/data-integrity-check.sql
```

3. **Identify Corruption Source**
- Check application logs
- Review recent deployments
- Check database logs

4. **Point-in-Time Recovery**
```bash
# Restore from backup before corruption occurred
./scripts/backup/restore-database.sh <backup-timestamp>
```

5. **Data Reconciliation**
```bash
# Manual data fixes if needed
# Document all changes made
```

**Expected Recovery Time**: 1-4 hours (depends on extent)
**Data Loss**: Variable (up to point of corruption)

## Complete System Failure

### Kubernetes Cluster Failure

**Scenario**: Complete cluster unavailability

**Detection**:
- All services down
- kubectl commands failing
- Cloud provider alerts

**Recovery Steps**:

1. **Assess Cluster State**
```bash
kubectl cluster-info
kubectl get nodes
```

2. **Contact Cloud Provider**
- Check cloud provider status page
- Open support ticket if provider issue

3. **Failover to DR Cluster** (if available)
```bash
# Update DNS to point to DR cluster
# Or update load balancer configuration

# Verify DR cluster is ready
kubectl get pods -n sec-latent --context=dr-cluster
```

4. **Rebuild Cluster from IaC**
```bash
# Using Terraform/Pulumi/etc
cd infrastructure/
terraform apply

# Redeploy applications
kubectl apply -k k8s/overlays/prod/
```

**Expected Recovery Time**: 1-2 hours
**Data Loss**: Minimal (if backups are recent and off-cluster)

### Complete Data Center Outage

**Scenario**: Entire data center or region unavailable

**Recovery Steps**:

1. **Activate DR Site**
```bash
# Switch DNS to DR region
# Update CDN origin

# Verify DR database is current
# Check replication lag if using streaming replication
```

2. **Restore from Offsite Backups**
```bash
# Download from S3/GCS
aws s3 cp s3://sec-latent-backups/latest/ /tmp/restore/ --recursive

# Restore databases
./scripts/recovery/restore-all-databases.sh /tmp/restore/
```

3. **Update External Integrations**
- Notify users of new URLs if changed
- Update webhook endpoints
- Update API keys if necessary

**Expected Recovery Time**: 2-6 hours
**Data Loss**: 5-60 minutes (depends on backup frequency)

## Post-Recovery Validation

### Validation Checklist

```bash
# 1. Run smoke tests
./scripts/health-checks/smoke-test.sh https://sec-latent.example.com

# 2. Verify all services running
kubectl get pods -n sec-latent
kubectl get svc -n sec-latent

# 3. Check data integrity
./scripts/health-checks/data-integrity-check.sh

# 4. Test critical user flows
./scripts/health-checks/critical-path-test.sh

# 5. Verify monitoring and alerts
curl -s https://grafana.example.com/api/health
curl -s https://prometheus.example.com/-/healthy

# 6. Check backup systems
./scripts/backup/verify-backup-systems.sh

# 7. Review logs for errors
kubectl logs -n sec-latent --all-containers --since=1h | grep -i error

# 8. Verify metrics collection
curl -s http://prometheus:9090/api/v1/query?query=up{job="backend-api"}
```

### Post-Incident Report

**Required Documentation**:
1. Incident timeline
2. Root cause analysis
3. Resolution steps taken
4. Data loss assessment
5. Lessons learned
6. Action items to prevent recurrence

**Template**: `/docs/templates/post-incident-report.md`

## Regular DR Testing

### Monthly DR Drills

Schedule regular disaster recovery drills:

```bash
# 1st Monday: Database restore test
# 2nd Monday: Application failover test
# 3rd Monday: Complete system recovery test
# 4th Monday: Security incident response test
```

### Automated Testing

```bash
# Run automated DR tests
./scripts/recovery/automated-dr-test.sh

# Generate DR test report
./scripts/recovery/generate-dr-report.sh
```

## Appendix

### Useful Commands Reference

```bash
# Quick diagnostics
kubectl get all -n sec-latent
kubectl top pods -n sec-latent
kubectl get events -n sec-latent --sort-by='.lastTimestamp' | head -20

# Force delete stuck pods
kubectl delete pod <pod-name> -n sec-latent --grace-period=0 --force

# Emergency maintenance mode
kubectl patch ingress sec-latent-ingress -n sec-latent \
    -p '{"metadata":{"annotations":{"nginx.ingress.kubernetes.io/default-backend":"maintenance-page"}}}'

# Quick backup
./scripts/backup/backup-database.sh production

# Check backup status
ls -lh /var/backups/sec-latent/$(date +%Y-%m-%d)/
```

### Emergency Shutdown Procedure

```bash
# 1. Enable maintenance mode
kubectl patch ingress sec-latent-ingress -n sec-latent \
    -p '{"metadata":{"annotations":{"nginx.ingress.kubernetes.io/custom-http-errors":"503"}}}'

# 2. Scale down gracefully
kubectl scale deployment sec-latent-backend -n sec-latent --replicas=0
kubectl scale deployment sec-latent-worker -n sec-latent --replicas=0
kubectl scale deployment sec-latent-frontend -n sec-latent --replicas=0

# 3. Final backup
./scripts/backup/backup-database.sh production

# 4. Stop databases
kubectl scale statefulset sec-latent-postgres -n sec-latent --replicas=0
kubectl scale statefulset sec-latent-redis -n sec-latent --replicas=0
```

---

**Document Version**: 1.0
**Last Updated**: 2024-10-18
**Next Review**: 2024-11-18
**Owner**: Infrastructure Team
