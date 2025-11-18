# SEC Latent Platform - Infrastructure Architecture

## Executive Summary

This document provides a comprehensive overview of the infrastructure architecture for the SEC filing analysis platform, designed for deployment on Railway with production-grade scalability, security, and reliability.

## Architecture Overview

### System Context (C4 Level 1)

```
┌─────────────────────────────────────────────────────────────────────┐
│                     SEC Latent Platform                              │
│                                                                       │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐     │
│  │   Web    │    │   API    │    │  Worker  │    │  Cache   │     │
│  │Frontend  │◄───│  Backend │◄───│  Queue   │◄───│  Redis   │     │
│  │(Next.js) │    │(FastAPI) │    │ (Celery) │    │          │     │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘     │
│                        │               │                             │
│                        └───────────────┴─────────────────┐          │
│                                                           │          │
│                                                    ┌──────▼─────┐   │
│                                                    │ PostgreSQL │   │
│                                                    │  Database  │   │
│                                                    └────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
          │                        │                        │
          │                        │                        │
    ┌─────▼─────┐          ┌─────▼─────┐          ┌──────▼─────┐
    │  SEC.gov  │          │   Claude  │          │  Supabase  │
    │    API    │          │    API    │          │   Storage  │
    └───────────┘          └───────────┘          └────────────┘
```

### Container Architecture (C4 Level 2)

```
┌────────────────────── Railway Platform ──────────────────────┐
│                                                                │
│  ┌─────────────────── Application Layer ───────────────────┐ │
│  │                                                           │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │ │
│  │  │ Frontend │  │ Backend  │  │  Worker  │  │  Beat   │ │ │
│  │  │  Next.js │  │ FastAPI  │  │  Celery  │  │Scheduler│ │ │
│  │  │  :3000   │  │  :8000   │  │          │  │         │ │ │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬────┘ │ │
│  │       │             │             │             │        │ │
│  └───────┼─────────────┼─────────────┼─────────────┼────────┘ │
│          │             │             │             │          │
│  ┌───────┴─────────────┴─────────────┴─────────────┴────────┐ │
│  │                   Load Balancer                           │ │
│  │                   (Railway Proxy)                         │ │
│  │                   SSL/TLS Termination                     │ │
│  └───────────────────────────────────────────────────────────┘ │
│          │                                                      │
│  ┌───────┴───────────── Data Layer ──────────────────────────┐ │
│  │                                                             │ │
│  │  ┌──────────────┐              ┌────────────────┐         │ │
│  │  │  PostgreSQL  │              │  Redis Cluster │         │ │
│  │  │   :5432      │              │     :6379      │         │ │
│  │  │              │              │                │         │ │
│  │  │ - Primary DB │              │ - Cache Layer  │         │ │
│  │  │ - Replication│              │ - Message Bus  │         │ │
│  │  │ - Backups    │              │ - Session Store│         │ │
│  │  └──────────────┘              └────────────────┘         │ │
│  │                                                             │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────── Monitoring Layer ─────────────────────────┐ │
│  │                                                               │ │
│  │  ┌───────────┐  ┌──────────┐  ┌─────────┐  ┌────────────┐ │ │
│  │  │Prometheus │  │ Grafana  │  │ Flower  │  │   Sentry   │ │ │
│  │  │  :9090    │  │  :3001   │  │  :5555  │  │  (Cloud)   │ │ │
│  │  └───────────┘  └──────────┘  └─────────┘  └────────────┘ │ │
│  │                                                               │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

## Key Design Decisions

### 1. Platform Selection: Railway

**Decision**: Use Railway as the primary deployment platform

**Rationale**:
- Automatic HTTPS/SSL certificate provisioning
- Built-in load balancing and health checks
- Simplified PostgreSQL and Redis provisioning
- Git-based deployments with automatic rollback
- Cost-effective for MVP to production scaling
- Zero-downtime deployments

**Trade-offs**:
- Less control than Kubernetes
- Vendor lock-in consideration
- Limited to Railway's infrastructure regions

### 2. Multi-Service Architecture

**Decision**: Deploy as separate services rather than monolithic

**Services**:
1. Frontend (Next.js): Port 3000
2. Backend API (FastAPI): Port 8000
3. Celery Worker: Background processing
4. Celery Beat: Task scheduling
5. PostgreSQL: Primary database
6. Redis: Cache and message broker

**Rationale**:
- Independent scaling per service
- Isolated failure domains
- Easier maintenance and updates
- Better resource utilization

### 3. Database Architecture

**Decision**: PostgreSQL 15 with connection pooling

**Configuration**:
- Primary instance with read replicas (for production)
- Connection pooling via PgBouncer
- Automated backups (daily, 30-day retention)
- Point-in-time recovery capability
- Partitioned tables for audit logs (7-year retention)

**Trade-offs**:
- More complex than single instance
- Higher cost for replication
- Requires monitoring and maintenance

### 4. Cache Strategy

**Decision**: Redis Cluster with cache-aside pattern

**Implementation**:
- Redis 7.x with persistence enabled
- Cache-aside pattern for API responses
- Write-through for session data
- TTL-based expiration
- LRU eviction policy

**Rationale**:
- Reduces database load by 60-80%
- Sub-millisecond response times
- Supports pub/sub for real-time features

## Infrastructure Components

### Compute Resources

| Service       | CPU    | Memory | Replicas | Scaling Strategy    |
|---------------|--------|--------|----------|---------------------|
| Frontend      | 0.5    | 512MB  | 2-4      | Horizontal (CPU)    |
| Backend       | 1.0    | 2GB    | 2-6      | Horizontal (CPU/Mem)|
| Worker        | 2.0    | 4GB    | 2-8      | Horizontal (Queue)  |
| Beat          | 0.25   | 256MB  | 1        | No scaling          |
| PostgreSQL    | 2.0    | 4GB    | 1-3      | Vertical + Read Rep |
| Redis         | 1.0    | 2GB    | 1-3      | Sentinel HA         |

### Storage Requirements

| Component     | Type      | Size    | Retention | Backup Frequency |
|---------------|-----------|---------|-----------|------------------|
| PostgreSQL    | SSD       | 100GB   | 7 years   | Daily            |
| Redis         | SSD       | 10GB    | N/A       | Snapshot         |
| Application   | Ephemeral | 20GB    | N/A       | N/A              |
| Logs          | Object    | 50GB    | 90 days   | Weekly           |
| Backups       | Object    | 500GB   | 1 year    | N/A              |

### Network Architecture

```
                    Internet
                       │
                       │ HTTPS (443)
                       │
        ┌──────────────▼──────────────┐
        │   CloudFlare CDN/WAF        │
        │   - DDoS Protection         │
        │   - Rate Limiting           │
        │   - SSL/TLS Termination     │
        └──────────────┬──────────────┘
                       │
                       │ HTTPS
                       │
        ┌──────────────▼──────────────┐
        │   Railway Load Balancer     │
        │   - Health Checks           │
        │   - Session Affinity        │
        │   - Auto Scaling            │
        └──────────────┬──────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
    ┌───▼────┐                    ┌───▼────┐
    │Frontend│                    │Backend │
    │Service │                    │Service │
    └───┬────┘                    └───┬────┘
        │                             │
        └──────────┬──────────────────┘
                   │
    ┌──────────────┴──────────────┐
    │                             │
┌───▼──────┐              ┌───────▼────┐
│PostgreSQL│              │   Redis    │
│ Private  │              │  Private   │
└──────────┘              └────────────┘
```

### Security Architecture

#### Network Isolation
- Public Subnet: Frontend, Load Balancer
- Private Subnet: Backend, Worker, Databases
- No direct internet access to data layer

#### Security Layers

1. **Perimeter Security**
   - CloudFlare WAF (Web Application Firewall)
   - DDoS protection
   - Bot detection and mitigation
   - Rate limiting (100 req/min per IP)

2. **Application Security**
   - OAuth 2.0 + JWT authentication
   - API key rotation (90 days)
   - Input validation and sanitization
   - SQL injection prevention (ORM)
   - XSS protection

3. **Data Security**
   - Encryption at rest (AES-256)
   - Encryption in transit (TLS 1.3)
   - Database encryption
   - Secrets management (Railway secrets)
   - PII data masking in logs

4. **Access Control**
   - RBAC (Role-Based Access Control)
   - Principle of least privilege
   - Service accounts with minimal permissions
   - Regular access audits

#### Compliance

- **SOC 2 Type II**: Infrastructure security controls
- **GDPR**: Data privacy and retention policies
- **SEC Rule 17a-4**: 7-year data retention for audit logs
- **CCPA**: California consumer privacy compliance

## Deployment Strategy

### Railway Deployment

#### Service Configuration

**railway.json** (Service manifest)
```json
{
  "services": {
    "frontend": {
      "build": {
        "dockerfile": "docker/Dockerfile.frontend"
      },
      "healthcheck": {
        "path": "/api/health",
        "interval": 30,
        "timeout": 10
      },
      "resources": {
        "cpu": 0.5,
        "memory": 512
      },
      "replicas": {
        "min": 2,
        "max": 4
      }
    },
    "backend": {
      "build": {
        "dockerfile": "docker/Dockerfile.backend"
      },
      "healthcheck": {
        "path": "/health",
        "interval": 30,
        "timeout": 10
      },
      "resources": {
        "cpu": 1.0,
        "memory": 2048
      },
      "replicas": {
        "min": 2,
        "max": 6
      }
    }
  }
}
```

### Deployment Environments

| Environment | Purpose              | Database     | Cache  | Monitoring |
|-------------|---------------------|--------------|--------|------------|
| Development | Local development   | PostgreSQL   | Redis  | Minimal    |
| Staging     | Pre-production test | PostgreSQL   | Redis  | Full       |
| Production  | Live environment    | PostgreSQL HA| Redis HA| Full      |

### Deployment Pipeline

```
┌─────────┐     ┌──────────┐     ┌────────────┐     ┌────────────┐
│   Git   │────▶│  Build   │────▶│    Test    │────▶│   Deploy   │
│  Push   │     │  Image   │     │  Security  │     │  Railway   │
└─────────┘     └──────────┘     └────────────┘     └────────────┘
                     │                  │                    │
                     ▼                  ▼                    ▼
              Docker Build      Trivy Scan          Rolling Update
              Multi-stage       SAST Analysis       Zero Downtime
              Optimization      Dependency Check    Health Checks
```

## Monitoring and Observability

### Metrics Collection

**Prometheus Metrics**:
- API request rate, latency, errors
- Database connection pool utilization
- Cache hit/miss rates
- Celery queue depth and processing time
- CPU, memory, disk utilization

**Custom Metrics**:
- SEC API rate limit usage
- Claude API token consumption
- Filing processing success/failure rate
- Signal extraction accuracy

### Logging Strategy

**Structured Logging**:
```json
{
  "timestamp": "2025-10-19T03:30:00Z",
  "level": "INFO",
  "service": "backend",
  "trace_id": "abc123",
  "user_id": "user_456",
  "action": "filing_analysis",
  "status": "success",
  "duration_ms": 1234,
  "metadata": {...}
}
```

**Log Aggregation**:
- ELK Stack (Elasticsearch, Logstash, Kibana)
- 90-day retention for operational logs
- 7-year retention for audit logs (compliance)

### Alerting

**Alert Categories**:

1. **Critical** (PagerDuty, immediate)
   - Service down
   - Database connection failure
   - Disk space >90%
   - Error rate >5%

2. **Warning** (Slack, 15 min)
   - High latency (>2s)
   - Cache miss rate >30%
   - Queue depth >1000

3. **Info** (Email, daily digest)
   - Deployment completed
   - Scaling events
   - Backup completed

## Disaster Recovery

### Backup Strategy

| Component    | Frequency | Retention | Recovery Time |
|--------------|-----------|-----------|---------------|
| Database     | Hourly    | 30 days   | < 1 hour      |
| Redis        | Daily     | 7 days    | < 15 minutes  |
| Application  | On deploy | 10 versions| < 5 minutes  |
| Logs         | Real-time | 90 days   | Immediate     |

### Recovery Procedures

1. **Database Failure**
   - Automatic failover to replica (< 30s)
   - Point-in-time recovery from backups
   - Maximum data loss: 1 hour

2. **Service Failure**
   - Automatic restart (3 attempts)
   - Rollback to previous version
   - Load balancer removes unhealthy instances

3. **Regional Outage**
   - Manual failover to backup region
   - DNS update to redirect traffic
   - RTO: 2 hours, RPO: 1 hour

## Cost Optimization

### Railway Pricing Estimate (Monthly)

| Service          | Resources        | Cost    |
|------------------|------------------|---------|
| Frontend         | 2x (0.5 CPU)     | $20     |
| Backend          | 2x (1.0 CPU)     | $60     |
| Worker           | 2x (2.0 CPU)     | $120    |
| PostgreSQL       | Pro plan         | $25     |
| Redis            | Hobby plan       | $5      |
| Monitoring       | Included         | $0      |
| **Total**        |                  | **$230**|

### Cost Optimization Strategies

1. **Right-sizing**: Monitor and adjust resource allocation
2. **Auto-scaling**: Scale down during off-peak hours
3. **Cache optimization**: Reduce database queries
4. **Batch processing**: Group SEC API calls
5. **CDN caching**: Reduce origin traffic by 70%

## Performance Targets

| Metric                    | Target      | Current  |
|---------------------------|-------------|----------|
| API Response Time (p95)   | < 500ms     | TBD      |
| Page Load Time (p95)      | < 2s        | TBD      |
| Database Query Time (avg) | < 50ms      | TBD      |
| Cache Hit Rate            | > 80%       | TBD      |
| Uptime (monthly)          | 99.9%       | TBD      |
| Error Rate                | < 0.1%      | TBD      |

## Scalability

### Horizontal Scaling Triggers

| Service  | Scale Up When            | Scale Down When         |
|----------|--------------------------|-------------------------|
| Frontend | CPU > 70% for 5 min      | CPU < 30% for 15 min    |
| Backend  | Request queue > 100      | Request queue < 20      |
| Worker   | Queue depth > 1000       | Queue depth < 100       |

### Capacity Planning

**Current Capacity** (2 backend replicas):
- 1,000 concurrent users
- 200 req/sec API throughput
- 100 filings/hour processing

**Target Capacity** (6 backend replicas):
- 5,000 concurrent users
- 1,000 req/sec API throughput
- 500 filings/hour processing

## Next Steps

1. **Phase 1**: Deploy to Railway staging environment
2. **Phase 2**: Load testing and performance optimization
3. **Phase 3**: Security audit and penetration testing
4. **Phase 4**: Production deployment with gradual rollout
5. **Phase 5**: Implement advanced monitoring and alerting

## Related Documents

- [Railway Deployment Guide](./deployment/RAILWAY_DEPLOYMENT.md)
- [Kubernetes Configuration](./deployment/KUBERNETES_SETUP.md)
- [Database Architecture](./database/DATABASE_ARCHITECTURE.md)
- [Redis Configuration](./cache/REDIS_ARCHITECTURE.md)
- [Security Architecture](./security/SECURITY_ARCHITECTURE.md)
- [Load Balancer Setup](./loadbalancer/NGINX_CONFIG.md)
