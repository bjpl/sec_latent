# Architecture Decision Records (ADR)

## Overview

This document captures all major architectural decisions made for the SEC Latent platform infrastructure, including rationale, alternatives considered, and trade-offs.

## ADR Format

Each decision record includes:
- **Title**: Short noun phrase describing the decision
- **Status**: Proposed | Accepted | Deprecated | Superseded
- **Context**: What is the issue we're trying to solve?
- **Decision**: What is the change we're actually proposing?
- **Consequences**: What becomes easier or harder because of this change?
- **Alternatives Considered**: What other options were evaluated?

---

## ADR-001: Railway as Primary Deployment Platform

**Status**: Accepted
**Date**: 2025-10-19
**Deciders**: Infrastructure Architecture Team

### Context

We need a deployment platform that:
- Provides managed PostgreSQL and Redis
- Supports Docker-based deployments
- Offers automatic SSL/TLS certificates
- Enables zero-downtime deployments
- Is cost-effective for MVP to production scaling
- Has simple configuration and maintenance

### Decision

Deploy the SEC Latent platform on Railway as the primary infrastructure platform.

### Rationale

Railway provides:
1. **Managed Services**: PostgreSQL and Redis fully managed with automatic backups
2. **Git-Based Deployments**: Automatic deployments from GitHub with rollback support
3. **Auto-Scaling**: Built-in horizontal and vertical scaling
4. **SSL/TLS**: Automatic certificate provisioning via Let's Encrypt
5. **Cost**: ~$230/month for production workload (lower than alternatives)
6. **Developer Experience**: Simple configuration via railway.json
7. **Health Checks**: Built-in health monitoring and automatic recovery

### Consequences

**Positive**:
- Reduced operational overhead (no Kubernetes cluster management)
- Faster time to production
- Built-in monitoring and alerting
- Automatic SSL certificate renewal
- Zero-downtime deployments by default

**Negative**:
- Vendor lock-in to Railway platform
- Less control compared to Kubernetes
- Limited to Railway's infrastructure regions
- May need migration path if outgrowing platform

**Risks**:
- Railway platform availability
- Pricing changes
- Feature limitations at scale

**Mitigation**:
- Maintain Kubernetes deployment option as backup
- Design architecture to be cloud-agnostic
- Use Docker for portability
- Monitor usage and costs monthly

### Alternatives Considered

1. **Kubernetes on AWS EKS**
   - Pros: Full control, scalability, multi-region
   - Cons: High operational complexity, ~$500/month cost, longer setup time
   - Rejected: Overkill for MVP, too expensive

2. **Heroku**
   - Pros: Simple PaaS, mature platform
   - Cons: Expensive (~$400/month), less modern features
   - Rejected: More expensive than Railway with fewer features

3. **Fly.io**
   - Pros: Good developer experience, competitive pricing
   - Cons: Smaller ecosystem, less mature managed services
   - Rejected: Railway has better PostgreSQL management

4. **Google Cloud Run**
   - Pros: Serverless, pay-per-use
   - Cons: Cold starts, complex for multi-service apps
   - Rejected: Not ideal for always-on services

---

## ADR-002: PostgreSQL 15 with Patroni for High Availability

**Status**: Accepted
**Date**: 2025-10-19
**Deciders**: Database Architecture Team

### Context

We need a relational database that:
- Handles complex queries for 150 signals per filing
- Supports 7-year audit log retention (SEC Rule 17a-4)
- Provides ACID guarantees
- Scales to millions of records
- Offers high availability (99.9% uptime)
- Supports JSON data for flexible signal storage

### Decision

Use PostgreSQL 15 as the primary database with Patroni for high availability and automatic failover.

### Rationale

PostgreSQL 15 provides:
1. **Advanced JSON Support**: JSONB for flexible signal storage
2. **Partitioning**: Time-based partitioning for audit logs
3. **Full-Text Search**: Built-in text search capabilities
4. **ACID Compliance**: Required for financial data integrity
5. **Replication**: Streaming replication for read scaling
6. **Extensions**: pgcrypto for encryption, pg_stat_statements for monitoring

Patroni adds:
1. **Automatic Failover**: < 30 seconds RTO
2. **Health Checks**: Continuous monitoring of database health
3. **Configuration Management**: Centralized via etcd/Consul
4. **Rolling Updates**: Zero-downtime PostgreSQL upgrades

### Consequences

**Positive**:
- Battle-tested database with 30+ years of development
- Rich ecosystem of tools and extensions
- Excellent JSON support (JSONB)
- Native partitioning for compliance requirements
- Strong community and documentation

**Negative**:
- More complex setup than managed services
- Requires expertise for performance tuning
- Write scaling requires sharding (future consideration)

**Performance Expectations**:
- 10,000+ QPS for read operations
- 1,000+ QPS for write operations
- Sub-50ms query latency (p95)
- 99.9% uptime with Patroni

### Alternatives Considered

1. **MongoDB**
   - Pros: Flexible schema, horizontal scaling
   - Cons: No ACID guarantees across documents, less query optimization
   - Rejected: Need ACID for financial data

2. **MySQL**
   - Pros: Good performance, wide adoption
   - Cons: Weaker JSON support, less advanced features
   - Rejected: PostgreSQL has better JSON and partitioning

3. **CockroachDB**
   - Pros: Distributed, strong consistency
   - Cons: Complex, expensive, learning curve
   - Rejected: Overkill for current scale

---

## ADR-003: Redis 7.x for Caching and Message Broker

**Status**: Accepted
**Date**: 2025-10-19
**Deciders**: Cache Architecture Team

### Context

We need a caching layer that:
- Reduces database load by 60-80%
- Provides sub-millisecond response times
- Supports pub/sub for real-time updates
- Serves as Celery message broker
- Handles rate limiting counters
- Stores session data

### Decision

Use Redis 7.x with Sentinel for high availability as the primary cache and message broker.

### Rationale

Redis 7.x provides:
1. **Performance**: Sub-millisecond latency for most operations
2. **Data Structures**: Strings, hashes, lists, sets, sorted sets, HyperLogLog
3. **Pub/Sub**: Real-time messaging for WebSocket updates
4. **Persistence**: AOF and RDB for durability
5. **Lua Scripting**: Atomic operations for rate limiting
6. **Cluster Mode**: Horizontal scaling (future)

Sentinel adds:
1. **Automatic Failover**: Promotes replica to master
2. **Monitoring**: Continuous health checks
3. **Configuration**: Dynamic reconfiguration

### Consequences

**Positive**:
- 80%+ cache hit rate expected
- Reduced database load significantly
- Enables real-time features via pub/sub
- Simplifies Celery setup (same technology)

**Negative**:
- In-memory storage limits dataset size
- Requires careful memory management
- Eviction policy must be configured properly

**Cache Strategy**:
- Cache-aside for API responses (5-60 min TTL)
- Write-through for session data
- TTL-based expiration
- LRU eviction when memory full

### Alternatives Considered

1. **Memcached**
   - Pros: Simple, fast
   - Cons: No persistence, limited data structures
   - Rejected: Need persistence and pub/sub

2. **KeyDB (Redis fork)**
   - Pros: Multi-threaded, faster
   - Cons: Less mature, smaller community
   - Rejected: Redis 7 performance sufficient

---

## ADR-004: Nginx as Load Balancer and Reverse Proxy

**Status**: Accepted
**Date**: 2025-10-19
**Deciders**: Network Architecture Team

### Context

We need a load balancer that:
- Terminates SSL/TLS connections
- Distributes traffic across backend instances
- Performs health checks
- Supports WebSocket connections
- Implements rate limiting
- Caches static assets

### Decision

Use Nginx as the primary load balancer and reverse proxy.

### Rationale

Nginx provides:
1. **Performance**: Can handle 10,000+ concurrent connections
2. **SSL/TLS**: Efficient SSL termination and HTTP/2 support
3. **Load Balancing**: Multiple algorithms (round-robin, least-conn, ip-hash)
4. **WebSocket**: Native support for WebSocket proxying
5. **Caching**: Built-in proxy caching for API responses
6. **Rate Limiting**: Flexible rate limiting with zones

### Consequences

**Positive**:
- Industry-standard solution with proven reliability
- Rich ecosystem of modules and integrations
- Excellent documentation and community
- Can handle 50,000+ req/sec per instance

**Negative**:
- Requires manual configuration (no auto-discovery)
- Reload needed for configuration changes
- Limited built-in monitoring (requires exporters)

**Configuration**:
- TLS 1.3 only
- HTTP/2 enabled
- Gzip compression for text content
- Proxy cache for GET requests (5 min TTL)
- Rate limiting: 100 req/min per IP (general), 1000 req/min for API

### Alternatives Considered

1. **HAProxy**
   - Pros: Advanced load balancing features
   - Cons: More complex configuration, no caching
   - Rejected: Nginx more versatile

2. **Envoy**
   - Pros: Modern, dynamic configuration, service mesh
   - Cons: Complex, overkill for current needs
   - Rejected: Too complex for current scale

3. **Railway's Built-in Load Balancer**
   - Pros: Fully managed, zero configuration
   - Cons: Limited customization
   - Rejected: Need custom rate limiting and caching

---

## ADR-005: Multi-Stage Docker Builds for Security and Size

**Status**: Accepted
**Date**: 2025-10-19
**Deciders**: Security & DevOps Team

### Context

We need Docker images that:
- Minimize attack surface
- Reduce image size
- Build quickly
- Don't include build dependencies in production
- Run as non-root user

### Decision

Use multi-stage Docker builds with security hardening for all services.

### Rationale

Multi-stage builds provide:
1. **Security**: Separate build-time and runtime dependencies
2. **Size**: 50-70% smaller images (400MB vs 1.2GB)
3. **Performance**: Faster deployments and scaling
4. **Best Practices**: Non-root user, minimal base image

Implementation:
- **Stage 1 (Builder)**: Install build tools, compile dependencies
- **Stage 2 (Runtime)**: Copy only runtime artifacts, minimal base image

### Consequences

**Positive**:
- Reduced attack surface (no build tools in production)
- Smaller images = faster deployments
- Lower storage costs
- Improved security posture

**Negative**:
- Slightly more complex Dockerfile
- Longer initial build time (but cached layers help)

**Security Hardening**:
```dockerfile
# Non-root user
RUN groupadd -r appuser && useradd -r -g appuser -u 1000 appuser
USER appuser

# Read-only filesystem (where possible)
# Minimal base image (alpine or distroless)
# No shells in production images
```

### Alternatives Considered

1. **Single-stage builds**
   - Pros: Simpler Dockerfile
   - Cons: Large images with build tools
   - Rejected: Security and size concerns

2. **Distroless images**
   - Pros: Even smaller, more secure
   - Cons: No shell for debugging
   - Rejected for now: Too restrictive, may adopt later

---

## ADR-006: CloudFlare for DDoS Protection and CDN

**Status**: Accepted
**Date**: 2025-10-19
**Deciders**: Security Architecture Team

### Context

We need protection against:
- DDoS attacks
- Bot traffic
- API abuse
- Global traffic optimization

### Decision

Use CloudFlare as the CDN and Web Application Firewall (WAF) in front of Railway.

### Rationale

CloudFlare provides:
1. **DDoS Protection**: Automatic mitigation of attacks
2. **WAF**: Protection against OWASP Top 10
3. **Bot Detection**: Challenges suspicious traffic
4. **CDN**: Global edge network (200+ locations)
5. **SSL/TLS**: Free SSL certificates
6. **Rate Limiting**: Additional layer of rate limiting
7. **Analytics**: Traffic insights and threat intelligence

### Consequences

**Positive**:
- Protection against attacks without infrastructure changes
- Improved global performance (CDN)
- Reduced origin traffic by 70%+
- Free SSL certificates with auto-renewal

**Negative**:
- Additional latency for uncached requests (~10-20ms)
- Potential vendor lock-in
- Cost for Pro plan ($20/month)

**Configuration**:
- WAF enabled with OWASP rules
- Bot fight mode enabled
- Browser integrity check
- Challenge passage for 5xx errors
- Page rules for caching static assets

### Alternatives Considered

1. **AWS CloudFront**
   - Pros: Tighter AWS integration
   - Cons: More expensive, complex setup
   - Rejected: CloudFlare more cost-effective

2. **No CDN/WAF**
   - Pros: Simplest setup
   - Cons: Vulnerable to attacks
   - Rejected: Unacceptable security risk

---

## ADR-007: OAuth 2.0 + JWT for Authentication

**Status**: Accepted
**Date**: 2025-10-19
**Deciders**: Security Architecture Team

### Context

We need authentication that:
- Supports third-party OAuth providers (Google, GitHub)
- Enables stateless API authentication
- Scales horizontally
- Supports role-based access control (RBAC)
- Provides token refresh capability

### Decision

Implement OAuth 2.0 for user authentication with JWT tokens for API access.

### Rationale

OAuth 2.0 + JWT provides:
1. **Standards-Based**: Industry standard for web authentication
2. **Stateless**: No server-side session storage
3. **Scalable**: Tokens validated without database lookup
4. **Flexible**: Supports multiple OAuth providers
5. **Secure**: Short-lived access tokens (15 min) + refresh tokens (7 days)
6. **RBAC**: Roles encoded in JWT claims

Implementation:
- OAuth providers: Google, GitHub (via Auth0 or similar)
- Access token: 15 minutes expiry
- Refresh token: 7 days expiry
- RS256 algorithm (asymmetric)
- Token rotation on refresh

### Consequences

**Positive**:
- No database lookup on every request
- Easy to add new OAuth providers
- Supports mobile and web clients
- Can revoke tokens via blacklist if needed

**Negative**:
- Cannot instantly revoke access tokens (must wait for expiry)
- JWT size larger than session IDs
- Requires secure key management

**Security Measures**:
- Short access token expiry
- Refresh token rotation
- Token blacklist for critical revocations
- HTTPS only
- Secure cookie flags (httpOnly, secure, sameSite)

### Alternatives Considered

1. **Session-based authentication**
   - Pros: Easy to revoke, simpler
   - Cons: Requires Redis lookups, harder to scale
   - Rejected: JWT more scalable

2. **API keys only**
   - Pros: Simple for programmatic access
   - Cons: No user authentication, less secure
   - Rejected: Need user auth, but support API keys too

---

## ADR-008: Celery with Redis for Background Job Processing

**Status**: Accepted
**Date**: 2025-10-19
**Deciders**: Backend Architecture Team

### Context

We need to process:
- SEC filing downloads (30-60 seconds)
- Signal extraction via Claude API (30-60 seconds)
- Scheduled data updates (periodic tasks)

Without blocking HTTP requests.

### Decision

Use Celery with Redis as the message broker for asynchronous task processing.

### Rationale

Celery provides:
1. **Asynchronous Processing**: Non-blocking API responses
2. **Distributed**: Scale workers independently
3. **Scheduling**: Celery Beat for periodic tasks
4. **Monitoring**: Flower for task monitoring
5. **Retry Logic**: Automatic retry with exponential backoff
6. **Priority Queues**: High/medium/low priority

Redis as broker:
- Already in infrastructure (no new dependency)
- Reliable message delivery
- Visibility into queues

### Consequences

**Positive**:
- API responds in <100ms, processing happens async
- Can scale workers independently of API servers
- Built-in retry and error handling
- Excellent monitoring with Flower

**Negative**:
- Additional complexity (more moving parts)
- Requires careful queue monitoring
- Can lose tasks if Redis fails (but Sentinel helps)

**Configuration**:
- 4 workers per instance
- 3 priority queues: high, medium, low
- Max 100 tasks per worker (then restart)
- 3 retries with exponential backoff

### Alternatives Considered

1. **RabbitMQ**
   - Pros: More features, better message guarantees
   - Cons: Another service to manage
   - Rejected: Redis sufficient for our needs

2. **AWS SQS**
   - Pros: Fully managed, no operational overhead
   - Cons: Vendor lock-in, higher latency
   - Rejected: Want platform-agnostic solution

---

## Summary of Key Decisions

| Decision | Technology | Rationale | Status |
|----------|-----------|-----------|--------|
| Deployment Platform | Railway | Managed services, cost-effective | Accepted |
| Database | PostgreSQL 15 + Patroni | ACID, JSON support, HA | Accepted |
| Cache | Redis 7.x + Sentinel | Performance, pub/sub, HA | Accepted |
| Load Balancer | Nginx | Mature, flexible, performant | Accepted |
| Container Strategy | Multi-stage Docker | Security, size optimization | Accepted |
| CDN/WAF | CloudFlare | DDoS protection, global CDN | Accepted |
| Authentication | OAuth 2.0 + JWT | Standards-based, scalable | Accepted |
| Background Jobs | Celery + Redis | Async processing, reliable | Accepted |

## Technology Evaluation Matrix

| Criterion | Weight | PostgreSQL | MongoDB | MySQL |
|-----------|--------|-----------|---------|-------|
| JSON Support | 20% | 9/10 | 10/10 | 7/10 |
| ACID Compliance | 25% | 10/10 | 6/10 | 10/10 |
| Partitioning | 15% | 9/10 | 8/10 | 8/10 |
| Community | 15% | 10/10 | 9/10 | 9/10 |
| Operational Complexity | 15% | 7/10 | 8/10 | 8/10 |
| Cost | 10% | 8/10 | 8/10 | 8/10 |
| **Total Score** | | **8.85** | 8.15 | 8.45 |

## Architecture Review Schedule

- **Monthly**: Review metrics and costs
- **Quarterly**: Evaluate scalability and performance
- **Annually**: Major architecture review and updates

## Next Steps

1. Implement all decisions in staging environment
2. Load testing to validate performance assumptions
3. Security audit before production deployment
4. Document operational procedures
5. Train team on new architecture

## Approval

This architecture has been reviewed and approved by:
- Infrastructure Team
- Security Team
- Development Team
- DevOps Team

Date: 2025-10-19
