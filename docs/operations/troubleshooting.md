# Troubleshooting Guide

## Overview

This guide provides solutions to common problems encountered in the SEC Filing Analysis System.

## Quick Diagnostic Commands

```bash
# System health check
curl https://api.sec-analysis.com/health

# Check all pods
kubectl get pods -n sec-analysis

# Check logs
kubectl logs -l app=api --tail=100
kubectl logs -l app=celery-worker --tail=100

# Check resource usage
kubectl top pods -n sec-analysis
kubectl top nodes

# Check database
kubectl exec -it deployment/api -- psql $DATABASE_URL -c "SELECT 1"

# Check Redis
redis-cli -h redis.sec-analysis.com PING
```

## API Issues

### Issue: API Returns 500 Internal Server Error

**Symptoms**:
- All API endpoints return 500 errors
- Health check fails
- Unable to process requests

**Diagnosis**:
```bash
# Check API logs
kubectl logs -l app=api --tail=50

# Check pod status
kubectl get pods -l app=api

# Check recent deployments
kubectl rollout history deployment/api
```

**Common Causes & Solutions**:

1. **Database Connection Failure**
   ```bash
   # Test database connection
   kubectl exec -it deployment/api -- \
     psql $DATABASE_URL -c "SELECT version()"

   # Check connection pool
   kubectl exec -it deployment/api -- \
     psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity"
   ```
   **Solution**: Restart API pods or scale database

2. **Missing Environment Variables**
   ```bash
   # Check secrets
   kubectl get secret sec-analysis-secrets -o yaml

   # Verify environment variables are loaded
   kubectl exec -it deployment/api -- env | grep SUPABASE
   ```
   **Solution**: Recreate secrets or update deployment

3. **Out of Memory**
   ```bash
   # Check memory usage
   kubectl top pods -l app=api

   # Check OOMKilled events
   kubectl describe pod <api-pod> | grep -A 10 "Last State"
   ```
   **Solution**: Increase memory limits or scale horizontally

### Issue: API Slow Response Times

**Symptoms**:
- Response times > 5 seconds
- Timeout errors
- Increased latency alerts

**Diagnosis**:
```bash
# Check API metrics
curl https://api.sec-analysis.com/metrics | grep api_request_duration

# Check database query times
kubectl exec -it deployment/api -- \
  psql $DATABASE_URL -c "SELECT query, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10"

# Check Redis latency
redis-cli -h redis.sec-analysis.com --latency
```

**Common Causes & Solutions**:

1. **Slow Database Queries**
   ```sql
   -- Find slow queries
   SELECT pid, query, state, query_start
   FROM pg_stat_activity
   WHERE state = 'active'
   AND query_start < now() - interval '5 seconds';
   ```
   **Solution**: Add indexes, optimize queries, or kill slow queries

2. **Cache Misses**
   ```bash
   # Check cache hit rate
   redis-cli -h redis.sec-analysis.com INFO stats | grep keyspace_hits
   ```
   **Solution**: Increase cache TTL or cache size

3. **Worker Overload**
   ```bash
   # Check worker count
   kubectl get pods -l app=celery-worker

   # Check task queue depth
   redis-cli -h redis.sec-analysis.com LLEN celery
   ```
   **Solution**: Scale workers horizontally

### Issue: Rate Limit Errors (429)

**Symptoms**:
- Clients receiving 429 Too Many Requests
- Rate limit headers showing 0 remaining

**Diagnosis**:
```bash
# Check NGINX rate limit stats
kubectl logs -l app=nginx-ingress | grep "limiting requests"

# Check client request patterns
kubectl logs -l app=api | grep "429" | cut -d' ' -f1 | sort | uniq -c
```

**Solution**:
```bash
# Increase rate limits (if legitimate traffic)
kubectl edit ingress api-ingress

# Add annotation:
# nginx.ingress.kubernetes.io/rate-limit: "200"

# Or block abusive IPs
kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: nginx-block-ips
data:
  block-ips.conf: |
    deny 192.168.1.100;
    deny 10.0.0.50;
EOF
```

## Celery Worker Issues

### Issue: Tasks Not Processing

**Symptoms**:
- Task queue depth increasing
- No task completions
- Workers idle

**Diagnosis**:
```bash
# Check worker status
kubectl get pods -l app=celery-worker
kubectl logs -l app=celery-worker --tail=50

# Check task queue
redis-cli -h redis.sec-analysis.com LLEN celery

# Check worker registration
celery -A src.pipeline.celery_tasks inspect active
```

**Common Causes & Solutions**:

1. **Workers Crashed**
   ```bash
   # Check pod restarts
   kubectl get pods -l app=celery-worker -o wide

   # Check crash logs
   kubectl logs <worker-pod> --previous
   ```
   **Solution**: Fix crash cause and restart workers

2. **Redis Connection Lost**
   ```bash
   # Test Redis connection
   redis-cli -h redis.sec-analysis.com PING

   # Check Redis logs
   kubectl logs -l app=redis
   ```
   **Solution**: Restart Redis or update connection settings

3. **Out of Memory/Resources**
   ```bash
   # Check resource usage
   kubectl top pods -l app=celery-worker

   # Check for OOMKilled
   kubectl describe pod <worker-pod> | grep -i "oom"
   ```
   **Solution**: Increase worker resources or reduce concurrency

### Issue: Task Timeouts

**Symptoms**:
- Tasks failing with timeout errors
- Long-running tasks being killed
- Model inference failures

**Diagnosis**:
```bash
# Check task execution times
kubectl logs -l app=celery-worker | grep "Task.*succeeded" | tail -20

# Check model loading times
kubectl logs -l app=celery-worker | grep "Loading model"

# Check GPU availability
kubectl exec -it <worker-pod> -- nvidia-smi
```

**Solutions**:

1. **Increase Task Timeout**
   ```python
   # Update in celery_tasks.py
   @app.task(bind=True, soft_time_limit=600, time_limit=900)
   def extract_signals_task(self, filing_id):
       ...
   ```

2. **Optimize Model Loading**
   ```bash
   # Mount model cache volume
   kubectl apply -f - <<EOF
   apiVersion: v1
   kind: PersistentVolumeClaim
   metadata:
     name: model-cache
   spec:
     accessModes:
       - ReadWriteMany
     resources:
       requests:
         storage: 50Gi
   EOF
   ```

3. **Route to Faster Model**
   ```bash
   # Lower complexity threshold temporarily
   kubectl set env deployment/api COMPLEXITY_THRESHOLD_HIGH=0.9
   ```

## Database Issues

### Issue: Database Connection Pool Exhausted

**Symptoms**:
- "Too many connections" errors
- API requests hanging
- Unable to acquire connection

**Diagnosis**:
```sql
-- Check current connections
SELECT count(*), state FROM pg_stat_activity GROUP BY state;

-- Check connection limits
SELECT * FROM pg_settings WHERE name = 'max_connections';

-- Find idle connections
SELECT pid, usename, application_name, state, state_change
FROM pg_stat_activity
WHERE state = 'idle'
AND state_change < now() - interval '1 hour';
```

**Solutions**:

1. **Kill Idle Connections**
   ```sql
   SELECT pg_terminate_backend(pid)
   FROM pg_stat_activity
   WHERE state = 'idle'
   AND state_change < now() - interval '1 hour';
   ```

2. **Increase Connection Pool**
   ```bash
   # Via Supabase dashboard
   # Settings → Database → Connection Pooling
   # Increase pool size to 40
   ```

3. **Enable Connection Pooling**
   ```bash
   # Update application config
   kubectl set env deployment/api \
     DATABASE_POOL_SIZE=20 \
     DATABASE_MAX_OVERFLOW=10
   ```

### Issue: Slow Query Performance

**Symptoms**:
- Queries taking > 5 seconds
- High database CPU usage
- API timeouts

**Diagnosis**:
```sql
-- Find slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Check missing indexes
SELECT schemaname, tablename, attname
FROM pg_stats
WHERE null_frac < 0.05
AND n_distinct > 1000
AND schemaname = 'public';

-- Check table sizes
SELECT schemaname, tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

**Solutions**:

1. **Add Missing Indexes**
   ```sql
   -- Example: Add composite index
   CREATE INDEX CONCURRENTLY idx_signals_filing_category
   ON signals(filing_id, category)
   WHERE confidence > 0.8;
   ```

2. **Optimize Queries**
   ```sql
   -- Use EXPLAIN ANALYZE
   EXPLAIN ANALYZE
   SELECT * FROM filings WHERE cik = '0000789019';

   -- Rewrite inefficient queries
   -- Before: SELECT * FROM signals WHERE filing_id IN (SELECT id FROM filings WHERE ...)
   -- After:  SELECT s.* FROM signals s INNER JOIN filings f ON s.filing_id = f.id WHERE ...
   ```

3. **Vacuum and Analyze**
   ```sql
   VACUUM ANALYZE filings;
   VACUUM ANALYZE signals;
   ```

### Issue: Database Disk Full

**Symptoms**:
- "No space left on device" errors
- Insert/update failures
- Database unavailable

**Diagnosis**:
```sql
-- Check database size
SELECT pg_size_pretty(pg_database_size('postgres'));

-- Check table sizes
SELECT schemaname, tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
  pg_size_pretty(pg_indexes_size(schemaname||'.'||tablename)) AS indexes_size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;
```

**Solutions**:

1. **Archive Old Data**
   ```sql
   -- Move old data to archive table
   CREATE TABLE filings_archive (LIKE filings INCLUDING ALL);

   INSERT INTO filings_archive
   SELECT * FROM filings WHERE filing_date < '2020-01-01';

   DELETE FROM filings WHERE filing_date < '2020-01-01';
   ```

2. **Increase Disk Size**
   ```bash
   # Via Supabase dashboard
   # Settings → Database → Storage
   # Increase disk size
   ```

3. **Vacuum Full**
   ```sql
   -- Requires maintenance window
   VACUUM FULL filings;
   VACUUM FULL signals;
   ```

## Model Inference Issues

### Issue: Model Loading Failures

**Symptoms**:
- "Model not found" errors
- Inference timeouts
- Worker crashes on model load

**Diagnosis**:
```bash
# Check model files
kubectl exec -it <worker-pod> -- ls -lh /models/

# Check disk space
kubectl exec -it <worker-pod> -- df -h

# Check model loading logs
kubectl logs <worker-pod> | grep "Loading model"
```

**Solutions**:

1. **Download Models**
   ```bash
   # Download missing models
   kubectl exec -it <worker-pod> -- python -c "
   from transformers import AutoModel, AutoTokenizer
   model = AutoModel.from_pretrained('microsoft/phi-3')
   tokenizer = AutoTokenizer.from_pretrained('microsoft/phi-3')
   "
   ```

2. **Mount Model Cache**
   ```yaml
   # Add volume mount to deployment
   volumes:
   - name: model-cache
     persistentVolumeClaim:
       claimName: model-cache-pvc
   volumeMounts:
   - name: model-cache
     mountPath: /models
   ```

3. **Increase Timeout**
   ```bash
   kubectl set env deployment/celery-worker \
     MODEL_LOAD_TIMEOUT=600
   ```

### Issue: GPU Out of Memory

**Symptoms**:
- "CUDA out of memory" errors
- Model inference failures
- Worker crashes

**Diagnosis**:
```bash
# Check GPU memory
kubectl exec -it <worker-pod> -- nvidia-smi

# Check model size
kubectl exec -it <worker-pod> -- \
  python -c "import torch; print(torch.cuda.memory_summary())"
```

**Solutions**:

1. **Clear GPU Cache**
   ```bash
   kubectl exec -it <worker-pod> -- \
     python -c "import torch; torch.cuda.empty_cache()"
   ```

2. **Reduce Batch Size**
   ```bash
   kubectl set env deployment/celery-worker \
     MODEL_BATCH_SIZE=1
   ```

3. **Use Smaller Model**
   ```bash
   # Route to Mistral instead of DeepSeek
   kubectl set env deployment/api \
     COMPLEXITY_THRESHOLD_HIGH=0.95
   ```

4. **Add More GPU Workers**
   ```bash
   kubectl scale deployment/celery-worker-gpu --replicas=5
   ```

## Network Issues

### Issue: External API Calls Failing

**Symptoms**:
- SEC EDGAR requests timing out
- Anthropic API errors
- DNS resolution failures

**Diagnosis**:
```bash
# Test external connectivity
kubectl exec -it deployment/api -- curl -I https://www.sec.gov

# Test DNS
kubectl exec -it deployment/api -- nslookup www.sec.gov

# Check egress rules
kubectl get networkpolicies -n sec-analysis
```

**Solutions**:

1. **Update Network Policy**
   ```yaml
   apiVersion: networking.k8s.io/v1
   kind: NetworkPolicy
   metadata:
     name: allow-external-api
   spec:
     podSelector:
       matchLabels:
         app: api
     policyTypes:
     - Egress
     egress:
     - to:
       - namespaceSelector: {}
     - ports:
       - protocol: TCP
         port: 443
   ```

2. **Configure Proxy**
   ```bash
   kubectl set env deployment/api \
     HTTP_PROXY=http://proxy.company.com:8080 \
     HTTPS_PROXY=http://proxy.company.com:8080
   ```

3. **Retry with Backoff**
   ```python
   # Verify retry logic is enabled
   @retry(
       stop=stop_after_attempt(3),
       wait=wait_exponential(multiplier=2, min=2, max=60)
   )
   def fetch_filing(url):
       ...
   ```

## Validation Issues

### Issue: FACT Validation Failures

**Symptoms**:
- High validation failure rate (>10%)
- Confidence scores too low
- Mathematical validation errors

**Diagnosis**:
```bash
# Check validation logs
kubectl logs -l app=celery-worker | grep "FACT validation"

# Check validation metrics
curl https://api.sec-analysis.com/metrics | grep validation_
```

**Solutions**:

1. **Lower Confidence Threshold**
   ```bash
   kubectl set env deployment/api FACT_CONFIDENCE_THRESHOLD=0.75
   ```

2. **Skip Validation for Low-Risk Claims**
   ```python
   # Update validation logic
   if risk_level == "low":
       run_validation = False
   ```

3. **Review Validation Rules**
   ```python
   # Check validation configuration
   kubectl exec -it deployment/api -- \
     cat /app/config/validation_config.yaml
   ```

## Performance Issues

### Issue: High CPU Usage

**Symptoms**:
- CPU usage > 80%
- Pods being throttled
- Slow response times

**Diagnosis**:
```bash
# Check CPU usage
kubectl top pods -n sec-analysis
kubectl top nodes

# Check CPU limits
kubectl describe pod <pod-name> | grep -A 5 "Limits:"
```

**Solutions**:

1. **Increase CPU Limits**
   ```bash
   kubectl set resources deployment/api --limits=cpu=4000m
   ```

2. **Scale Horizontally**
   ```bash
   kubectl scale deployment/api --replicas=10
   ```

3. **Enable Auto-scaling**
   ```yaml
   apiVersion: autoscaling/v2
   kind: HorizontalPodAutoscaler
   metadata:
     name: api-hpa
   spec:
     scaleTargetRef:
       apiVersion: apps/v1
       kind: Deployment
       name: api
     minReplicas: 3
     maxReplicas: 20
     metrics:
     - type: Resource
       resource:
         name: cpu
         target:
           type: Utilization
           averageUtilization: 70
   ```

### Issue: High Memory Usage

**Symptoms**:
- Memory usage > 90%
- OOMKilled events
- Pods restarting frequently

**Diagnosis**:
```bash
# Check memory usage
kubectl top pods -n sec-analysis

# Check OOMKilled events
kubectl get events -n sec-analysis | grep OOMKilled
```

**Solutions**:

1. **Increase Memory Limits**
   ```bash
   kubectl set resources deployment/api --limits=memory=8Gi
   ```

2. **Fix Memory Leaks**
   ```python
   # Profile memory usage
   import tracemalloc
   tracemalloc.start()
   # ... code ...
   snapshot = tracemalloc.take_snapshot()
   top_stats = snapshot.statistics('lineno')
   for stat in top_stats[:10]:
       print(stat)
   ```

3. **Enable Memory Profiling**
   ```bash
   kubectl set env deployment/api PYTHONMALLOC=malloc
   ```

---

**Document Version**: 1.0
**Last Updated**: 2025-10-18
**Owner**: Operations Team
**Review Cycle**: Quarterly
