# System Architecture

## Overview

The SEC Filing Analysis System is designed as a modular, scalable platform for extracting, validating, and analyzing latent signals from SEC filings.

## Architecture Principles

1. **Modularity**: Each component is independently deployable and testable
2. **Scalability**: Horizontal scaling through Celery worker pools
3. **Reliability**: Multi-layer validation and error handling
4. **Cost Efficiency**: 95% local processing reduces cloud costs by 98%
5. **Maintainability**: Clear separation of concerns and comprehensive documentation

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Client Applications                          │
│                    (REST API, Python SDK, CLI)                       │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           API Gateway                                │
│                          (FastAPI)                                   │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                ┌────────────────┼────────────────┐
                │                │                │
                ▼                ▼                ▼
      ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
      │  Ingestion  │  │ Extraction  │  │ Validation  │
      │   Service   │  │   Service   │  │   Service   │
      └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
             │                │                │
             └────────────────┼────────────────┘
                              │
                              ▼
                   ┌────────────────────┐
                   │   Celery Queue     │
                   │   (Redis Broker)   │
                   └─────────┬──────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
          ▼                  ▼                  ▼
    ┌──────────┐      ┌──────────┐      ┌──────────┐
    │ Worker 1 │      │ Worker 2 │      │ Worker N │
    └────┬─────┘      └────┬─────┘      └────┬─────┘
         │                 │                 │
         └─────────────────┼─────────────────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
            ▼              ▼              ▼
      ┌──────────┐   ┌──────────┐   ┌──────────┐
      │ Supabase │   │  DuckDB  │   │ ChromaDB │
      │(Postgres)│   │(Analytics)│   │ (Vectors)│
      └──────────┘   └──────────┘   └──────────┘
```

## Component Details

### 1. API Gateway (FastAPI)

**Responsibilities**:
- HTTP request routing
- Authentication & authorization
- Rate limiting
- Request validation
- Response formatting

**Endpoints**:
- `/filings`: Filing management
- `/signals`: Signal extraction
- `/validate`: Validation operations
- `/health`: System health checks
- `/metrics`: Prometheus metrics

**Technology**:
- FastAPI 0.104+
- Pydantic for validation
- JWT authentication
- CORS middleware

### 2. Ingestion Service

**Responsibilities**:
- SEC EDGAR data fetching
- Filing parsing (HTML/XBRL)
- Section extraction
- Rate limit compliance

**Components**:
- `SECEdgarConnector`: Main connector class
- `FilingParser`: HTML/XBRL parser
- `SectionExtractor`: Section identification
- `RateLimiter`: SEC compliance

**Data Flow**:
```
CIK → Fetch Filing List → Download Content → Parse Sections → Store Metadata
```

**Error Handling**:
- Retry with exponential backoff
- Circuit breaker for SEC API
- Fallback to cached data

### 3. Signal Extraction Service

**Responsibilities**:
- Extract 150 signals from filings
- Multi-model processing
- Confidence scoring
- Signal aggregation

**Signal Categories**:
1. **Financial (50 signals)**: Revenue trends, margins, ratios
2. **Sentiment (30 signals)**: Management tone, forward-looking statements
3. **Risk (40 signals)**: Risk factors, uncertainties, contingencies
4. **Management (30 signals)**: Executive changes, compensation, governance

**Extraction Pipeline**:
```
Filing Data → Category Extractors → Signal Aggregation → Confidence Scoring
```

**Parallelization**:
- Category extractors run in parallel
- Worker pool for concurrent processing
- Signal-level caching

### 4. Model Routing Service

**Responsibilities**:
- Assess task complexity
- Route to appropriate model
- Handle model failures
- Fallback management

**Routing Logic**:
```python
complexity = assess_complexity(filing)
if complexity < 0.4:
    model = Mistral7B  # Fast track
elif complexity < 0.7:
    model = MistralDeepSeek  # Hybrid
else:
    model = DeepSeekR1  # Deep analysis
```

**Model Tiers**:
- **Tier 1**: Phi3 (classification) - <1s
- **Tier 2A**: Mistral 7B (fast) - ~5s
- **Tier 2B**: DeepSeek-R1 (deep) - 15-20s
- **Tier 2C**: 5-model ensemble - 12-18s
- **Tier 2D**: Hybrid (Mistral+DeepSeek) - 10-15s

### 5. Validation Service

**FACT Framework**:
- **Mathematical**: Qwen2.5-coder for calculations
- **Logical**: DeepSeek-R1 for reasoning
- **Critical**: Claude 3.5 for high-stakes decisions

**GOALIE Protection**:
- Risk assessment (6 categories)
- Confidence scoring (multi-model agreement)
- Prediction adjustment (conservative scaling)

**Validation Pipeline**:
```
Claim → FACT Validation → GOALIE Protection → Metrics Tracking → Output
```

### 6. Task Queue (Celery)

**Architecture**:
- Redis as message broker
- Redis as result backend
- Worker pool with autoscaling
- Priority queues

**Task Types**:
1. `fetch_company_filings`: Fetch filing metadata
2. `fetch_and_parse_filing`: Parse filing content
3. `extract_signals`: Extract all signals
4. `validate_signals`: Run validation
5. `aggregate_results`: Combine outputs

**Workflow Example**:
```python
workflow = (
    fetch_filings.s(cik) |
    group([parse_filing.s(url) for url in filing_urls]) |
    chord([extract_signals.s() for filing in filings])(aggregate.s())
)
```

### 7. Storage Layer

#### Supabase (PostgreSQL)
- Primary structured data storage
- ACID compliance for critical data
- Real-time subscriptions
- Row-level security

**Tables**:
- `filings`: Filing metadata
- `signals`: Extracted signal values
- `validations`: Validation results
- `models`: Model performance metrics

#### DuckDB
- Analytics and aggregations
- OLAP queries
- Large-scale data scanning
- Parquet file integration

**Use Cases**:
- Historical trend analysis
- Signal correlation studies
- Performance benchmarking
- Bulk data exports

#### ChromaDB
- Vector embeddings
- Semantic search
- Document similarity
- RAG applications

**Collections**:
- `filing_embeddings`: Document vectors
- `section_embeddings`: Section-level vectors
- `signal_patterns`: Pattern embeddings

## Data Flow

### Filing Processing Flow

```
1. API Request
   └─▶ Validate parameters
       └─▶ Queue task

2. Ingestion
   └─▶ Fetch from SEC EDGAR
       └─▶ Parse HTML/XBRL
           └─▶ Extract sections
               └─▶ Store metadata (Supabase)

3. Classification
   └─▶ Phi3 complexity assessment
       └─▶ Route to appropriate model tier
           └─▶ Cache decision

4. Signal Extraction
   └─▶ Parallel category extraction
       └─▶ Financial signals (50)
       └─▶ Sentiment signals (30)
       └─▶ Risk signals (40)
       └─▶ Management signals (30)
       └─▶ Aggregate results
           └─▶ Store signals (Supabase + DuckDB)

5. Validation
   └─▶ FACT mathematical validation
       └─▶ FACT logical validation
           └─▶ FACT critical validation
               └─▶ GOALIE risk assessment
                   └─▶ GOALIE confidence scoring
                       └─▶ Adjusted predictions
                           └─▶ Store validation report

6. Response
   └─▶ Aggregate results
       └─▶ Format response
           └─▶ Return to client
```

## Scalability

### Horizontal Scaling

**Celery Workers**:
- Add workers to handle increased load
- Workers auto-discover tasks
- Load balancing via Redis
- Worker health monitoring

**Database Scaling**:
- Supabase: Read replicas for queries
- DuckDB: Partitioned data files
- ChromaDB: Sharded collections

### Vertical Scaling

**Resource Allocation**:
- GPU workers for model inference
- Memory optimization for large filings
- CPU allocation per worker
- Disk I/O optimization

## Reliability & Fault Tolerance

### Error Handling

**Retry Strategies**:
- Exponential backoff for transient errors
- Circuit breaker for downstream services
- Dead letter queue for failed tasks
- Manual retry interface

**Monitoring**:
- Task success/failure rates
- Latency percentiles (P50, P95, P99)
- Error classification and alerting
- Resource utilization tracking

### Data Consistency

**Transactions**:
- ACID guarantees for critical operations
- Idempotent task design
- Deduplication mechanisms
- Conflict resolution strategies

### Disaster Recovery

**Backups**:
- Daily database backups (Supabase)
- Point-in-time recovery (PITR)
- Configuration version control
- Model checkpoint versioning

**Recovery Procedures**:
1. Database restoration from backup
2. Task queue drain and restart
3. Cache invalidation
4. Health check verification

## Security

### Authentication & Authorization

**API Security**:
- JWT tokens with expiration
- Role-based access control (RBAC)
- API key management
- Rate limiting per client

**Data Security**:
- Encryption at rest (AES-256)
- Encryption in transit (TLS 1.3)
- Row-level security (Supabase)
- Audit logging

### Network Security

**Isolation**:
- Private network for backend services
- Public API gateway only
- VPN access for admin operations
- Firewall rules

## Performance Optimization

### Caching Strategy

**Levels**:
1. **Application Cache**: Parsed filings (1 hour TTL)
2. **Model Cache**: Classification results (24 hours TTL)
3. **Signal Cache**: Extracted signals (permanent, invalidate on update)
4. **Embedding Cache**: Vector embeddings (permanent)

**Cache Invalidation**:
- Time-based expiration
- Event-based invalidation
- Manual purge capability
- Version-based invalidation

### Query Optimization

**Database Indexes**:
- B-tree indexes on CIK, filing_date
- GIN indexes for full-text search
- Partial indexes for active filings
- Covering indexes for common queries

**Query Patterns**:
- Batch operations over single queries
- Connection pooling
- Prepared statements
- Query result pagination

## Monitoring & Observability

### Metrics Collection

**System Metrics**:
- CPU, memory, disk usage
- Network I/O
- Task queue depth
- Worker utilization

**Application Metrics**:
- Request latency (P50, P95, P99)
- Error rates by endpoint
- Signal extraction accuracy
- Model inference time

**Business Metrics**:
- Filings processed per hour
- Signal extraction coverage
- Validation pass rates
- Cost per filing

### Logging

**Structured Logging**:
```json
{
  "timestamp": "2025-10-18T20:00:00Z",
  "level": "INFO",
  "service": "signal_extraction",
  "task_id": "abc123",
  "cik": "0000789019",
  "message": "Extracted 150 signals",
  "latency_ms": 22000,
  "model": "mistral-7b"
}
```

**Log Aggregation**:
- Centralized logging (ELK stack)
- Log retention: 90 days
- Search and filtering
- Alert rules on patterns

## Deployment Architecture

### Development Environment
- Docker Compose for local stack
- Separate database instances
- Debug logging enabled
- Hot reload for code changes

### Staging Environment
- Kubernetes cluster (3 nodes)
- Replicated databases
- Production-like data
- Performance testing

### Production Environment
- Kubernetes cluster (10+ nodes)
- High availability (HA) setup
- Multi-region deployment
- Auto-scaling policies

## Technology Decisions

### Why FastAPI?
- Async support for I/O-bound tasks
- Automatic OpenAPI documentation
- Type validation with Pydantic
- High performance

### Why Celery?
- Mature task queue solution
- Flexible routing and priorities
- Monitoring tools (Flower)
- Integration with Python ecosystem

### Why Supabase?
- PostgreSQL with modern API
- Real-time capabilities
- Built-in authentication
- Generous free tier

### Why DuckDB?
- In-process OLAP database
- Fast analytical queries
- Parquet integration
- Zero-copy data loading

## Future Enhancements

### Q2 2025
- Streaming ingestion for real-time filings
- GraphQL API alongside REST
- Advanced caching with Redis Cluster
- Multi-region deployment

### Q3 2025
- Machine learning model fine-tuning pipeline
- Real-time dashboard with WebSockets
- Advanced anomaly detection
- Integration with market data feeds

### Q4 2025
- Automated compliance reporting
- Natural language query interface
- Predictive analytics features
- White-label deployment options

---

**Document Version**: 1.0
**Last Updated**: 2025-10-18
**Owner**: Architecture Team
**Review Cycle**: Quarterly
