# Deployment Guide

## Overview

This guide covers deploying the SEC Filing Analysis System to production environments using Docker, Kubernetes, and managed cloud services.

## Prerequisites

### Required Software
- Docker 24.0+
- Docker Compose 2.20+
- Kubernetes 1.28+ (for production)
- kubectl CLI
- Helm 3.12+
- Python 3.11+
- Git

### Required Accounts
- Supabase account (or PostgreSQL server)
- Redis instance (or managed service)
- Cloud provider account (AWS/GCP/Azure)
- Anthropic API key (for Claude models)

### System Requirements

**Development**:
- CPU: 4 cores
- RAM: 16GB
- Disk: 50GB SSD
- GPU: Optional (for local model inference)

**Production**:
- CPU: 8+ cores per worker
- RAM: 32GB+ per worker
- Disk: 200GB+ SSD
- GPU: 24GB VRAM (for DeepSeek-R1)

## Development Deployment

### 1. Environment Setup

Clone repository:
```bash
git clone https://github.com/your-org/sec-latent.git
cd sec-latent
```

Create environment file:
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
```bash
# Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# API Keys
SONNET_API_KEY=your_anthropic_key
HAIKU_API_KEY=your_anthropic_key

# SEC EDGAR
SEC_USER_AGENT=Your Company Name contact@example.com

# Environment
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
```

### 2. Docker Compose

Start services:
```bash
docker-compose up -d
```

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=development
    env_file:
      - .env
    depends_on:
      - redis
    volumes:
      - ./src:/app/src
    command: uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

  celery-worker:
    build: .
    environment:
      - ENVIRONMENT=development
    env_file:
      - .env
    depends_on:
      - redis
    volumes:
      - ./src:/app/src
    command: celery -A src.pipeline.celery_tasks worker --loglevel=info --concurrency=4

  celery-beat:
    build: .
    environment:
      - ENVIRONMENT=development
    env_file:
      - .env
    depends_on:
      - redis
    command: celery -A src.pipeline.celery_tasks beat --loglevel=info

  redis:
    image: redis:7.2-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  flower:
    image: mher/flower:2.0
    ports:
      - "5555:5555"
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      - redis

volumes:
  redis_data:
```

Verify services:
```bash
# Check API
curl http://localhost:8000/health

# Check Flower (Celery monitor)
open http://localhost:5555
```

### 3. Database Setup

Run migrations:
```bash
# Using Supabase migrations
npx supabase db push

# Or run SQL directly
psql $SUPABASE_URL < migrations/001_initial_schema.sql
```

Seed test data (optional):
```bash
python scripts/seed_data.py --environment development
```

### 4. Verification

Run health checks:
```bash
# API health
curl http://localhost:8000/health

# Process test filing
curl -X POST http://localhost:8000/filings/process \
  -H "Content-Type: application/json" \
  -d '{
    "cik": "0000789019",
    "form_type": "10-K",
    "filing_date": "2024-02-06"
  }'
```

## Staging Deployment

### 1. Kubernetes Cluster Setup

Create cluster (using AWS EKS example):
```bash
eksctl create cluster \
  --name sec-analysis-staging \
  --region us-east-1 \
  --nodegroup-name standard-workers \
  --node-type m5.2xlarge \
  --nodes 3 \
  --nodes-min 2 \
  --nodes-max 5 \
  --managed
```

Configure kubectl:
```bash
aws eks update-kubeconfig \
  --region us-east-1 \
  --name sec-analysis-staging
```

### 2. Install Dependencies

Install NGINX Ingress Controller:
```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install nginx-ingress ingress-nginx/ingress-nginx
```

Install Cert-Manager (for TLS):
```bash
helm repo add jetstack https://charts.jetstack.io
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --set installCRDs=true
```

Install Prometheus & Grafana:
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack
```

### 3. Create Kubernetes Resources

**Namespace**:
```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: sec-analysis
```

**ConfigMap**:
```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: sec-analysis-config
  namespace: sec-analysis
data:
  ENVIRONMENT: "staging"
  LOG_LEVEL: "INFO"
  CELERY_WORKER_CONCURRENCY: "4"
```

**Secrets**:
```bash
kubectl create secret generic sec-analysis-secrets \
  --from-literal=supabase-url=$SUPABASE_URL \
  --from-literal=supabase-key=$SUPABASE_KEY \
  --from-literal=sonnet-api-key=$SONNET_API_KEY \
  --namespace sec-analysis
```

**Deployment - API**:
```yaml
# api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  namespace: sec-analysis
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
      - name: api
        image: your-registry/sec-analysis-api:v1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          valueFrom:
            configMapKeyRef:
              name: sec-analysis-config
              key: ENVIRONMENT
        envFrom:
        - secretRef:
            name: sec-analysis-secrets
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
```

**Deployment - Celery Workers**:
```yaml
# celery-worker-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: celery-worker
  namespace: sec-analysis
spec:
  replicas: 5
  selector:
    matchLabels:
      app: celery-worker
  template:
    metadata:
      labels:
        app: celery-worker
    spec:
      containers:
      - name: celery-worker
        image: your-registry/sec-analysis-worker:v1.0.0
        command: ["celery", "-A", "src.pipeline.celery_tasks", "worker", "--loglevel=info"]
        env:
        - name: CELERY_WORKER_CONCURRENCY
          valueFrom:
            configMapKeyRef:
              name: sec-analysis-config
              key: CELERY_WORKER_CONCURRENCY
        envFrom:
        - secretRef:
            name: sec-analysis-secrets
        resources:
          requests:
            memory: "4Gi"
            cpu: "2000m"
          limits:
            memory: "8Gi"
            cpu: "4000m"
```

**Service**:
```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: api-service
  namespace: sec-analysis
spec:
  selector:
    app: api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
```

**Ingress**:
```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-ingress
  namespace: sec-analysis
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api-staging.sec-analysis.com
    secretName: api-tls
  rules:
  - host: api-staging.sec-analysis.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 80
```

### 4. Deploy Application

Apply Kubernetes resources:
```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/celery-worker-deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
```

Verify deployment:
```bash
# Check pods
kubectl get pods -n sec-analysis

# Check logs
kubectl logs -f deployment/api -n sec-analysis

# Check ingress
kubectl get ingress -n sec-analysis
```

## Production Deployment

### 1. High Availability Setup

**Multi-region deployment**:
- Primary region: us-east-1
- Secondary region: us-west-2
- Database replication across regions
- Global load balancer (AWS Route 53)

**Auto-scaling configuration**:
```yaml
# hpa.yaml (Horizontal Pod Autoscaler)
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
  namespace: sec-analysis
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
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### 2. Database Configuration

**Supabase Production Setup**:
- Enable connection pooling (PgBouncer)
- Configure read replicas
- Set up automated backups (daily + PITR)
- Enable point-in-time recovery
- Configure monitoring and alerting

**DuckDB Configuration**:
```python
# config/duckdb_production.py
DUCKDB_CONFIG = {
    'memory_limit': '32GB',
    'threads': 16,
    'temp_directory': '/mnt/duckdb-temp',
    'extensions': ['parquet', 'json'],
    'checkpoint_threshold': '10GB'
}
```

### 3. Redis Configuration

**Redis Cluster Setup**:
```yaml
# redis-cluster-values.yaml
cluster:
  enabled: true
  slaveCount: 3

master:
  persistence:
    enabled: true
    size: 20Gi

sentinel:
  enabled: true
  quorum: 2
```

Deploy Redis:
```bash
helm install redis bitnami/redis \
  --namespace sec-analysis \
  --values redis-cluster-values.yaml
```

### 4. Security Configuration

**Network Policies**:
```yaml
# network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-network-policy
  namespace: sec-analysis
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
```

**Pod Security Policy**:
```yaml
# pod-security-policy.yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: sec-analysis-psp
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
  - ALL
  runAsUser:
    rule: MustRunAsNonRoot
  seLinux:
    rule: RunAsAny
  fsGroup:
    rule: RunAsAny
```

### 5. Monitoring Setup

**Prometheus ServiceMonitor**:
```yaml
# service-monitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: api-metrics
  namespace: sec-analysis
spec:
  selector:
    matchLabels:
      app: api
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
```

**Grafana Dashboards**:
- System health dashboard
- API performance dashboard
- Celery task queue dashboard
- Database performance dashboard

### 6. Logging Configuration

**Fluent Bit DaemonSet**:
```yaml
# fluent-bit-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluent-bit-config
  namespace: sec-analysis
data:
  fluent-bit.conf: |
    [INPUT]
        Name tail
        Path /var/log/containers/*.log
        Parser docker
        Tag kube.*

    [FILTER]
        Name kubernetes
        Match kube.*

    [OUTPUT]
        Name es
        Match *
        Host elasticsearch.logging.svc
        Port 9200
```

### 7. Backup Strategy

**Database Backups**:
```bash
# Automated daily backups
0 2 * * * /usr/local/bin/backup-database.sh

# backup-database.sh
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump $DATABASE_URL | gzip > /backups/db_$DATE.sql.gz
aws s3 cp /backups/db_$DATE.sql.gz s3://backups/sec-analysis/
```

**Config Backups**:
```bash
# Backup Kubernetes configs
kubectl get all --all-namespaces -o yaml > k8s-backup-$(date +%Y%m%d).yaml
```

## CI/CD Pipeline

### GitHub Actions Workflow

**.github/workflows/deploy.yml**:
```yaml
name: Deploy to Production

on:
  push:
    tags:
      - 'v*'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Run tests
      run: |
        pip install -r requirements.txt
        pytest tests/ --cov=src --cov-report=xml

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Build Docker image
      run: |
        docker build -t $ECR_REGISTRY/sec-analysis:$GITHUB_SHA .
        docker push $ECR_REGISTRY/sec-analysis:$GITHUB_SHA

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
    - name: Deploy to Kubernetes
      run: |
        kubectl set image deployment/api api=$ECR_REGISTRY/sec-analysis:$GITHUB_SHA
        kubectl rollout status deployment/api
```

## Rollback Procedures

### Quick Rollback

```bash
# Rollback to previous version
kubectl rollout undo deployment/api -n sec-analysis

# Rollback to specific revision
kubectl rollout undo deployment/api --to-revision=3 -n sec-analysis

# Check rollout status
kubectl rollout status deployment/api -n sec-analysis
```

### Database Rollback

```bash
# Restore from backup
psql $DATABASE_URL < backups/db_20250218_020000.sql

# Or use Supabase PITR
# (via Supabase dashboard or API)
```

## Troubleshooting

### Common Issues

**Pods not starting**:
```bash
# Check pod events
kubectl describe pod <pod-name> -n sec-analysis

# Check logs
kubectl logs <pod-name> -n sec-analysis

# Check resource constraints
kubectl top pods -n sec-analysis
```

**Database connection errors**:
```bash
# Test connection
kubectl exec -it <api-pod> -n sec-analysis -- \
  psql $DATABASE_URL -c "SELECT 1"

# Check secrets
kubectl get secret sec-analysis-secrets -n sec-analysis -o yaml
```

**High latency**:
```bash
# Check metrics
kubectl top pods -n sec-analysis

# Scale up
kubectl scale deployment/api --replicas=10 -n sec-analysis

# Check ingress
kubectl describe ingress api-ingress -n sec-analysis
```

---

**Document Version**: 1.0
**Last Updated**: 2025-10-18
**Owner**: DevOps Team
**Review Cycle**: Quarterly
