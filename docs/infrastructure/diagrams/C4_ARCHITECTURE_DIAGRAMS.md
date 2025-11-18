# C4 Architecture Diagrams

## Overview

C4 (Context, Containers, Components, Code) model diagrams for the SEC Latent platform architecture.

## Level 1: System Context Diagram

Shows how the SEC Latent platform fits into the world around it, including users and external systems.

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                       │
│                         System Context                                │
│                                                                       │
│                                                                       │
│    ┌──────────┐                                      ┌──────────┐   │
│    │Financial │                                      │ SEC.gov  │   │
│    │ Analyst  │────────┐                    ┌───────│   API    │   │
│    └──────────┘        │                    │       └──────────┘   │
│                        │                    │                       │
│    ┌──────────┐        │                    │       ┌──────────┐   │
│    │Portfolio │        │                    │       │ Claude   │   │
│    │ Manager  │────────┤                    ├───────│   API    │   │
│    └──────────┘        │                    │       └──────────┘   │
│                        ▼                    ▼                       │
│    ┌──────────┐   ┌────────────────────────────┐   ┌──────────┐   │
│    │Compliance│──▶│   SEC Latent Platform     │◀──│ Supabase │   │
│    │ Officer  │   │                            │   │ Storage  │   │
│    └──────────┘   │ Analyzes SEC filings and   │   └──────────┘   │
│                   │ extracts 150 signals for   │                   │
│    ┌──────────┐   │ investment decision making │   ┌──────────┐   │
│    │ System   │──▶│                            │──▶│  Email   │   │
│    │  Admin   │   └────────────────────────────┘   │  SMTP    │   │
│    └──────────┘                                     └──────────┘   │
│                                                                       │
│   Users                  System Boundary            External Systems│
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘

Key:
────▶ Uses / Interacts with
```

## Level 2: Container Diagram

Shows the high-level technology choices and how containers communicate.

```
┌──────────────────────────── SEC Latent Platform ────────────────────────┐
│                                                                           │
│  ┌────────────────────────── Presentation Layer ──────────────────────┐ │
│  │                                                                      │ │
│  │  ┌──────────────────────────────────────────────────────────────┐  │ │
│  │  │                    Web Frontend                               │  │ │
│  │  │                    (Next.js, React)                          │  │ │
│  │  │                                                               │  │ │
│  │  │  - Dashboard UI                                              │  │ │
│  │  │  - Filing Search                                             │  │ │
│  │  │  - Signal Visualization                                      │  │ │
│  │  │  - Authentication UI                                         │  │ │
│  │  │                                                               │  │ │
│  │  │  [Container: Next.js SPA]                                    │  │ │
│  │  └────────────────────┬─────────────────────────────────────────┘  │ │
│  │                       │ HTTPS/WebSocket                            │ │
│  └───────────────────────┼─────────────────────────────────────────────┘ │
│                          │                                               │
│  ┌───────────────────────┼────── Application Layer ───────────────────┐ │
│  │                       │                                             │ │
│  │  ┌────────────────────▼──────────────────────────────────────────┐ │ │
│  │  │                    API Gateway                                 │ │ │
│  │  │                 (FastAPI, Python)                             │ │ │
│  │  │                                                                │ │ │
│  │  │  - REST API endpoints                                         │ │ │
│  │  │  - WebSocket server                                           │ │ │
│  │  │  - Authentication/Authorization                               │ │ │
│  │  │  - Rate limiting                                              │ │ │
│  │  │  - Input validation                                           │ │ │
│  │  │                                                                │ │ │
│  │  │  [Container: FastAPI Application]                             │ │ │
│  │  └────────────┬───────────────┬───────────────┬──────────────────┘ │ │
│  │               │               │               │                    │ │
│  │  ┌────────────▼──────┐ ┌─────▼──────┐ ┌─────▼─────────────────┐  │ │
│  │  │  Worker Processes │ │   Celery   │ │   Celery Beat         │  │ │
│  │  │  (Celery, Python) │ │   Workers  │ │   Scheduler           │  │ │
│  │  │                   │ │            │ │                       │  │ │
│  │  │  - SEC data fetch │ │  - Signal  │ │  - Scheduled jobs    │  │ │
│  │  │  - Filing parsing │ │  extraction│ │  - Periodic updates  │  │ │
│  │  │  - AI analysis    │ │  - Analysis│ │  - Cleanup tasks     │  │ │
│  │  │                   │ │  - Reports │ │                       │  │ │
│  │  │  [Container: x4]  │ │ [Container]│ │  [Container: x1]      │  │ │
│  │  └────────────┬──────┘ └─────┬──────┘ └─────┬─────────────────┘  │ │
│  │               │               │               │                    │ │
│  └───────────────┼───────────────┼───────────────┼────────────────────┘ │
│                  │               │               │                      │
│  ┌───────────────┼───────────────┼───────────────┼──── Data Layer ───┐ │
│  │               │               │               │                    │ │
│  │  ┌────────────▼───────────────▼───────────────▼─────────────────┐ │ │
│  │  │                    Redis Cluster                              │ │ │
│  │  │                   (Cache & Message Broker)                    │ │ │
│  │  │                                                                │ │ │
│  │  │  - API response cache                                         │ │ │
│  │  │  - Session storage                                            │ │ │
│  │  │  - Celery message queue                                       │ │ │
│  │  │  - Rate limiting counters                                     │ │ │
│  │  │                                                                │ │ │
│  │  │  [Container: Redis 7.x with Sentinel HA]                      │ │ │
│  │  └────────────────────────────────────────────────────────────────┘ │ │
│  │                                                                      │ │
│  │  ┌──────────────────────────────────────────────────────────────┐  │ │
│  │  │                    PostgreSQL Database                        │  │ │
│  │  │                  (Primary + Read Replicas)                    │  │ │
│  │  │                                                                │  │ │
│  │  │  - Companies & filings                                        │  │ │
│  │  │  - Extracted signals (150 per filing)                         │  │ │
│  │  │  - Analysis results                                           │  │ │
│  │  │  - User data & API keys                                       │  │ │
│  │  │  - Audit logs (7-year retention)                              │  │ │
│  │  │                                                                │  │ │
│  │  │  [Container: PostgreSQL 15 with replication]                  │  │ │
│  │  └──────────────────────────────────────────────────────────────┘  │ │
│  │                                                                      │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
│  ┌────────────────────────── Monitoring Layer ──────────────────────────┐ │
│  │                                                                        │ │
│  │  ┌───────────┐  ┌──────────┐  ┌─────────┐  ┌────────────────────┐  │ │
│  │  │Prometheus │  │ Grafana  │  │ Flower  │  │   Sentry (Cloud)   │  │ │
│  │  │           │  │          │  │  Celery │  │   Error Tracking   │  │ │
│  │  │ Metrics   │  │Dashboard │  │ Monitor │  │                    │  │ │
│  │  └───────────┘  └──────────┘  └─────────┘  └────────────────────┘  │ │
│  │                                                                        │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘

Technology Stack:
- Frontend: Next.js, React, TypeScript, TailwindCSS
- Backend: FastAPI, Python 3.11, Pydantic
- Workers: Celery, Python 3.11
- Cache: Redis 7.x with Sentinel
- Database: PostgreSQL 15 with Patroni
- Monitoring: Prometheus, Grafana, Sentry
- Infrastructure: Railway, Docker, Kubernetes
```

## Level 3: Component Diagram - Backend API

Shows the internal structure of the Backend API container.

```
┌────────────────────────── Backend API Container ──────────────────────────┐
│                           (FastAPI Application)                            │
│                                                                             │
│  ┌──────────────────────── API Layer ─────────────────────────────────┐   │
│  │                                                                      │   │
│  │  ┌───────────────┐  ┌───────────────┐  ┌────────────────────────┐ │   │
│  │  │ Auth Router   │  │ Filing Router │  │  Analysis Router       │ │   │
│  │  │               │  │               │  │                        │ │   │
│  │  │ - /auth/login │  │ - /filings/*  │  │  - /analysis/*         │ │   │
│  │  │ - /auth/token │  │ - /companies/*│  │  - /signals/*          │ │   │
│  │  └───────┬───────┘  └───────┬───────┘  └────────┬───────────────┘ │   │
│  │          │                   │                    │                 │   │
│  └──────────┼───────────────────┼────────────────────┼─────────────────┘   │
│             │                   │                    │                     │
│  ┌──────────┼───────────────────┼────────────────────┼─── Service Layer ─┐│
│  │          │                   │                    │                    ││
│  │  ┌───────▼───────┐  ┌────────▼────────┐  ┌───────▼──────────────┐   ││
│  │  │ Auth Service  │  │ Filing Service  │  │  Analysis Service    │   ││
│  │  │               │  │                 │  │                      │   ││
│  │  │ - JWT tokens  │  │ - CRUD ops      │  │  - Signal extract    │   ││
│  │  │ - OAuth flow  │  │ - Search        │  │  - AI analysis       │   ││
│  │  │ - Permissions │  │ - Filtering     │  │  - Model selection   │   ││
│  │  └───────┬───────┘  └────────┬────────┘  └───────┬──────────────┘   ││
│  │          │                   │                    │                   ││
│  └──────────┼───────────────────┼────────────────────┼───────────────────┘│
│             │                   │                    │                     │
│  ┌──────────┼───────────────────┼────────────────────┼── Repository Layer┐│
│  │          │                   │                    │                    ││
│  │  ┌───────▼───────┐  ┌────────▼────────┐  ┌───────▼──────────────┐   ││
│  │  │ User Repo     │  │ Filing Repo     │  │  Signal Repo         │   ││
│  │  │               │  │                 │  │                      │   ││
│  │  │ - DB queries  │  │ - DB queries    │  │  - DB queries        │   ││
│  │  │ - Caching     │  │ - Caching       │  │  - Caching           │   ││
│  │  └───────┬───────┘  └────────┬────────┘  └───────┬──────────────┘   ││
│  │          │                   │                    │                   ││
│  └──────────┼───────────────────┼────────────────────┼───────────────────┘│
│             │                   │                    │                     │
│  ┌──────────┼───────────────────┼────────────────────┼──── Data Access ──┐│
│  │          │                   │                    │                    ││
│  │  ┌───────▼───────┐  ┌────────▼────────┐  ┌───────▼──────────────┐   ││
│  │  │ PostgreSQL    │  │  Redis Cache    │  │  External APIs       │   ││
│  │  │  Connection   │  │   Connection    │  │                      │   ││
│  │  │               │  │                 │  │  - SEC.gov API       │   ││
│  │  │ - SQLAlchemy  │  │ - Redis client  │  │  - Claude API        │   ││
│  │  │ - Connection  │  │ - Cache mgmt    │  │  - Supabase Storage  │   ││
│  │  │   pooling     │  │                 │  │                      │   ││
│  │  └───────────────┘  └─────────────────┘  └──────────────────────┘   ││
│  │                                                                        ││
│  └────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│  ┌─────────────────────── Cross-Cutting Concerns ────────────────────────┐│
│  │                                                                         ││
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌───────┐ ││
│  │  │ Logging  │  │  Metrics │  │  Tracing │  │Rate Limit │  │ Auth  │ ││
│  │  │          │  │          │  │          │  │           │  │ Midw. │ ││
│  │  │ Middleware│  │Middleware│  │Middleware│  │Middleware │  │       │ ││
│  │  └──────────┘  └──────────┘  └──────────┘  └───────────┘  └───────┘ ││
│  │                                                                         ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

Component Responsibilities:

1. Routers: HTTP request handling, validation, response formatting
2. Services: Business logic, orchestration, domain operations
3. Repositories: Data access abstraction, caching strategies
4. Data Access: Direct database/cache/API communication
5. Middleware: Cross-cutting concerns (logging, auth, metrics)
```

## Level 4: Code Diagram - Signal Extraction Component

Shows the internal structure of the signal extraction process.

```
┌──────────────────── Signal Extraction Component ───────────────────────┐
│                                                                          │
│  Entry Point: extract_signals(filing_id: int) -> List[Signal]          │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  1. FilingRetriever                                            │    │
│  │     - get_filing_by_id(filing_id)                             │    │
│  │     - fetch_from_cache() -> Optional[Filing]                  │    │
│  │     - fetch_from_database() -> Filing                         │    │
│  │     - parse_html_to_text() -> str                             │    │
│  └─────────────────────┬──────────────────────────────────────────┘    │
│                        │                                                │
│                        ▼                                                │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  2. FilingSectionizer                                          │    │
│  │     - split_into_sections(text: str) -> Dict[str, str]        │    │
│  │     - identify_section_headers()                               │    │
│  │     - extract_section_content()                                │    │
│  │     Sections: MD&A, Financial Statements, Risk Factors, etc.  │    │
│  └─────────────────────┬──────────────────────────────────────────┘    │
│                        │                                                │
│                        ▼                                                │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  3. ModelSelector                                              │    │
│  │     - select_model(section: str) -> ModelConfig                │    │
│  │     - calculate_complexity(text: str) -> float                 │    │
│  │     - choose_claude_version() -> "sonnet"|"haiku"|"opus"      │    │
│  │     Rules:                                                      │    │
│  │       - Complexity > 0.7: Opus                                 │    │
│  │       - Complexity 0.4-0.7: Sonnet                             │    │
│  │       - Complexity < 0.4: Haiku                                │    │
│  └─────────────────────┬──────────────────────────────────────────┘    │
│                        │                                                │
│                        ▼                                                │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  4. SignalExtractorOrchestrator                                │    │
│  │     - orchestrate_extraction() -> List[Signal]                 │    │
│  │     - parallel_extract_by_category()                           │    │
│  │     - merge_and_deduplicate()                                  │    │
│  │                                                                 │    │
│  │     Coordinates 4 extractors in parallel:                      │    │
│  │     ┌─────────────────┬─────────────┬────────────┬──────────┐ │    │
│  │     │                 │             │            │          │ │    │
│  │     ▼                 ▼             ▼            ▼          │ │    │
│  │  Financial      Sentiment       Risk      Management       │ │    │
│  │  Extractor      Extractor    Extractor    Extractor        │ │    │
│  │  (50 signals)   (30 signals) (40 signals) (30 signals)     │ │    │
│  │                                                              │ │    │
│  └──────────────────────┬───────────────────────────────────────┘ │    │
│                         │                                          │    │
│                         ▼                                          │    │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  5. FinancialSignalExtractor                                   │    │
│  │     - extract(section: str, model: str) -> List[Signal]        │    │
│  │     - build_prompt(section: str) -> str                        │    │
│  │     - call_claude_api(prompt: str) -> str                      │    │
│  │     - parse_response(response: str) -> List[Signal]            │    │
│  │     - validate_signals(signals: List[Signal]) -> List[Signal]  │    │
│  │                                                                 │    │
│  │     Extracted Signals (50):                                    │    │
│  │       - Revenue growth, margins, cash flow                     │    │
│  │       - Debt levels, liquidity ratios                          │    │
│  │       - Asset turnover, ROE, ROA                               │    │
│  │       - Dividend policy, share buybacks                        │    │
│  └─────────────────────┬──────────────────────────────────────────┘    │
│                        │                                                │
│                        ▼                                                │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  6. SignalValidator                                            │    │
│  │     - validate_all(signals: List[Signal]) -> List[Signal]      │    │
│  │     - check_data_types()                                       │    │
│  │     - verify_confidence_scores()                               │    │
│  │     - remove_duplicates()                                      │    │
│  │     - flag_anomalies()                                         │    │
│  └─────────────────────┬──────────────────────────────────────────┘    │
│                        │                                                │
│                        ▼                                                │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  7. SignalPersister                                            │    │
│  │     - save_to_database(signals: List[Signal])                  │    │
│  │     - cache_results(signals: List[Signal])                     │    │
│  │     - log_extraction_metrics()                                 │    │
│  │     - send_notifications()                                     │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  Return: List[Signal] (150 signals total)                              │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘

Data Flow:
Filing ID → Retrieve Filing → Sectionize → Select Model → Extract Signals
  → Validate → Persist → Return Signals

Error Handling:
- Retry logic for API failures (3 attempts)
- Fallback to simpler model on timeout
- Partial success handling (some signals extracted)
- Comprehensive logging for debugging
```

## Deployment Diagram

Shows how the system is deployed to Railway platform.

```
┌────────────────────────── Railway Platform ──────────────────────────┐
│                                                                        │
│  ┌────────────────────── Region: US-East ─────────────────────────┐  │
│  │                                                                  │  │
│  │  ┌───────────────── Load Balancer (Automated) ──────────────┐  │  │
│  │  │  - SSL/TLS Termination                                    │  │  │
│  │  │  - Health Checks                                          │  │  │
│  │  │  - Auto-scaling                                           │  │  │
│  │  └────────────────────┬──────────────────────────────────────┘  │  │
│  │                       │                                          │  │
│  │  ┌────────────────────┼──── Application Services ────────────┐  │  │
│  │  │                    │                                       │  │  │
│  │  │  ┌─────────────────▼─────────┐  ┌─────────────────────┐  │  │  │
│  │  │  │  Frontend Service         │  │  Backend Service    │  │  │  │
│  │  │  │  - Railway Service ID: 1  │  │  - Service ID: 2    │  │  │  │
│  │  │  │  - Replicas: 2-4 (auto)   │  │  - Replicas: 2-6    │  │  │  │
│  │  │  │  - CPU: 0.5, Mem: 512MB   │  │  - CPU: 1, Mem: 2GB │  │  │  │
│  │  │  └───────────────────────────┘  └─────────────────────┘  │  │  │
│  │  │                                                            │  │  │
│  │  │  ┌─────────────────────────┐  ┌─────────────────────────┐│  │  │
│  │  │  │  Worker Service         │  │  Beat Service           ││  │  │
│  │  │  │  - Service ID: 3        │  │  - Service ID: 4        ││  │  │
│  │  │  │  - Replicas: 2-8 (auto) │  │  - Replicas: 1 (fixed)  ││  │  │
│  │  │  │  - CPU: 2, Mem: 4GB     │  │  - CPU: 0.25, Mem: 256MB││  │  │
│  │  │  └─────────────────────────┘  └─────────────────────────┘│  │  │
│  │  │                                                            │  │  │
│  │  └────────────────────────────────────────────────────────────┘  │  │
│  │                                                                    │  │
│  │  ┌───────────────────── Data Services ─────────────────────────┐ │  │
│  │  │                                                               │ │  │
│  │  │  ┌─────────────────────────┐  ┌─────────────────────────┐  │ │  │
│  │  │  │  PostgreSQL Pro         │  │  Redis Hobby            │  │ │  │
│  │  │  │  - Managed by Railway   │  │  - Managed by Railway   │  │ │  │
│  │  │  │  - Auto backups         │  │  - Persistence enabled  │  │ │  │
│  │  │  │  - Connection pooling   │  │  - Max memory: 2GB      │  │ │  │
│  │  │  │  - Storage: 100GB       │  │  - Eviction: allkeys-lru│  │ │  │
│  │  │  └─────────────────────────┘  └─────────────────────────┘  │ │  │
│  │  │                                                               │ │  │
│  │  └───────────────────────────────────────────────────────────────┘ │  │
│  │                                                                      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  ┌───────────────────── External Services ─────────────────────────────┐  │
│  │                                                                       │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │  │
│  │  │  CloudFlare  │  │   Sentry     │  │  Supabase    │             │  │
│  │  │     CDN      │  │   Errors     │  │   Storage    │             │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘             │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘

Deployment Configuration:
- Platform: Railway (PaaS)
- Region: US-East
- Environment: Production
- Deployment: Git-based (main branch)
- Rollback: Automated on health check failure
- Cost: ~$230/month
```

## Data Flow Diagram

Shows how data flows through the system during filing analysis.

```
                           User Request
                                │
                                ▼
    ┌───────────────────────────────────────────────────────┐
    │  1. User submits filing analysis request             │
    │     GET /api/filings/AAPL/10-K/latest                │
    └──────────────────────┬────────────────────────────────┘
                           │
                           ▼
    ┌───────────────────────────────────────────────────────┐
    │  2. API Gateway (FastAPI)                            │
    │     - Authenticate request (JWT)                      │
    │     - Rate limit check (Redis)                        │
    │     - Input validation                                │
    └──────────────────────┬────────────────────────────────┘
                           │
                           ▼
    ┌───────────────────────────────────────────────────────┐
    │  3. Check Cache (Redis)                               │
    │     Key: "filing:analysis:AAPL:10-K:latest"          │
    │                                                        │
    │     Hit? ──Yes──> Return cached result (5min TTL)    │
    │      │                                                 │
    │     No                                                 │
    └──────┴───────────────────────────────────────────────┘
           │
           ▼
    ┌──────────────────────────────────────────────────────┐
    │  4. Query Database (PostgreSQL)                       │
    │     - Find company by ticker (AAPL)                   │
    │     - Get latest 10-K filing                          │
    │     - Check if analysis exists                        │
    │                                                        │
    │     Exists? ──Yes──> Return from DB + Cache          │
    │      │                                                 │
    │     No                                                 │
    └──────┴──────────────────────────────────────────────┘
           │
           ▼
    ┌──────────────────────────────────────────────────────┐
    │  5. Queue Analysis Task (Celery + Redis)             │
    │     Task: analyze_filing_async(filing_id=123)        │
    │     Queue: high_priority                              │
    │     Return: task_id=abc-123                          │
    └──────────────────────┬─────────────────────────────────┘
                           │
                           ▼
    ┌──────────────────────────────────────────────────────┐
    │  6. Return 202 Accepted                              │
    │     Response: {                                       │
    │       "status": "processing",                         │
    │       "task_id": "abc-123",                          │
    │       "websocket_url": "/ws/tasks/abc-123"           │
    │     }                                                 │
    └──────────────────────────────────────────────────────┘
                           │
                           ▼
    ┌──────────────────────────────────────────────────────┐
    │  7. Celery Worker Picks Up Task                      │
    │     - Fetch filing from SEC.gov (if needed)          │
    │     - Parse HTML to text                             │
    │     - Split into sections                            │
    └──────────────────────┬─────────────────────────────────┘
                           │
                           ▼
    ┌──────────────────────────────────────────────────────┐
    │  8. Signal Extraction (Parallel)                     │
    │     ┌──────────────────────────────────────────┐     │
    │     │ Financial (50) → Claude Sonnet          │     │
    │     │ Sentiment (30) → Claude Haiku           │     │
    │     │ Risk (40)      → Claude Sonnet          │     │
    │     │ Management(30) → Claude Haiku           │     │
    │     └──────────────────────────────────────────┘     │
    │     Concurrent API calls with rate limiting          │
    └──────────────────────┬─────────────────────────────────┘
                           │
                           ▼
    ┌──────────────────────────────────────────────────────┐
    │  9. Validate & Store Results                         │
    │     - Validate 150 signals                           │
    │     - Store in PostgreSQL                            │
    │     - Cache in Redis (1 hour TTL)                    │
    │     - Update filing status = "completed"             │
    └──────────────────────┬─────────────────────────────────┘
                           │
                           ▼
    ┌──────────────────────────────────────────────────────┐
    │  10. Notify User (WebSocket)                         │
    │      Message: {                                       │
    │        "event": "analysis_complete",                  │
    │        "task_id": "abc-123",                         │
    │        "filing_id": 123,                             │
    │        "signals_count": 150                          │
    │      }                                                │
    └──────────────────────┬─────────────────────────────────┘
                           │
                           ▼
    ┌──────────────────────────────────────────────────────┐
    │  11. User Retrieves Results                          │
    │      GET /api/analysis/123                           │
    │      Response: 150 signals with confidence scores    │
    └──────────────────────────────────────────────────────┘

Timeline:
- Steps 1-6: ~100ms (synchronous)
- Steps 7-10: ~30-60s (asynchronous)
- Total user-perceived latency: 100ms (with async processing)
```

## Security Architecture Diagram

Shows security controls at each layer.

```
┌──────────────────────── Security Layers ─────────────────────────────┐
│                                                                        │
│  Layer 1: Perimeter ─────────────────────────────────────────────┐   │
│  │  ┌──────────────────────────────────────────────────────────┐ │   │
│  │  │  CloudFlare WAF                                          │ │   │
│  │  │  - DDoS Protection (automatic)                           │ │   │
│  │  │  - Bot Detection (challenge)                             │ │   │
│  │  │  - Rate Limiting (100 req/min per IP)                    │ │   │
│  │  │  - Geo-blocking (configurable)                           │ │   │
│  │  │  - SSL/TLS Termination (TLS 1.3)                        │ │   │
│  │  └──────────────────────────────────────────────────────────┘ │   │
│  └──────────────────────────────┬────────────────────────────────┘   │
│                                 │                                     │
│  Layer 2: Network ──────────────┼─────────────────────────────────┐  │
│  │  ┌────────────────────────────▼────────────────────────────┐   │  │
│  │  │  VPC / Private Network                                  │   │  │
│  │  │  - Private subnets for data layer                       │   │  │
│  │  │  - Security groups (firewall rules)                     │   │  │
│  │  │  - No direct internet access for databases              │   │  │
│  │  └────────────────────────────┬────────────────────────────┘   │  │
│  └──────────────────────────────┼─────────────────────────────────┘  │
│                                 │                                     │
│  Layer 3: Application ──────────┼─────────────────────────────────┐  │
│  │  ┌────────────────────────────▼────────────────────────────┐   │  │
│  │  │  API Gateway Security                                   │   │  │
│  │  │  - OAuth 2.0 + JWT authentication                       │   │  │
│  │  │  - API key management                                   │   │  │
│  │  │  - Input validation (Pydantic)                          │   │  │
│  │  │  - XSS/CSRF protection                                  │   │  │
│  │  │  - Rate limiting (per user)                             │   │  │
│  │  │  - RBAC (viewer, analyst, admin)                        │   │  │
│  │  └────────────────────────────┬────────────────────────────┘   │  │
│  └──────────────────────────────┼─────────────────────────────────┘  │
│                                 │                                     │
│  Layer 4: Data ─────────────────┼─────────────────────────────────┐  │
│  │  ┌────────────────────────────▼────────────────────────────┐   │  │
│  │  │  Data Security                                          │   │  │
│  │  │  - Encryption at rest (AES-256)                         │   │  │
│  │  │  - Encryption in transit (TLS 1.3)                      │   │  │
│  │  │  - Database encryption (pgcrypto)                       │   │  │
│  │  │  - Secrets management (Railway/K8s secrets)             │   │  │
│  │  │  - PII data masking in logs                             │   │  │
│  │  └─────────────────────────────────────────────────────────┘   │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                        │
│  Layer 5: Monitoring ──────────────────────────────────────────────┐  │
│  │  ┌──────────────────────────────────────────────────────────┐  │  │
│  │  │  Security Monitoring                                     │  │  │
│  │  │  - Audit logs (7-year retention)                         │  │  │
│  │  │  - Intrusion detection                                   │  │  │
│  │  │  - Anomaly detection                                     │  │  │
│  │  │  - Security alerts (PagerDuty)                           │  │  │
│  │  │  - Compliance reporting (SOC 2, GDPR)                    │  │  │
│  │  └──────────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

## Technology Stack Summary

```
┌─────────────────────── Technology Stack ──────────────────────────┐
│                                                                     │
│  Frontend:                                                         │
│    - Next.js 14                                                    │
│    - React 18                                                      │
│    - TypeScript 5.x                                                │
│    - TailwindCSS 3.x                                               │
│                                                                     │
│  Backend:                                                          │
│    - FastAPI 0.104+                                                │
│    - Python 3.11                                                   │
│    - Pydantic 2.x                                                  │
│    - SQLAlchemy 2.x                                                │
│    - Celery 5.x                                                    │
│                                                                     │
│  Database:                                                         │
│    - PostgreSQL 15                                                 │
│    - Patroni (HA)                                                  │
│    - PgBouncer (pooling)                                           │
│                                                                     │
│  Cache & Queue:                                                    │
│    - Redis 7.x                                                     │
│    - Redis Sentinel (HA)                                           │
│                                                                     │
│  Infrastructure:                                                   │
│    - Railway (primary)                                             │
│    - Kubernetes (optional)                                         │
│    - Docker & Docker Compose                                       │
│    - Nginx (load balancer)                                         │
│                                                                     │
│  Monitoring:                                                       │
│    - Prometheus                                                    │
│    - Grafana                                                       │
│    - Sentry                                                        │
│    - ELK Stack                                                     │
│                                                                     │
│  Security:                                                         │
│    - CloudFlare WAF                                                │
│    - OAuth 2.0 + JWT                                               │
│    - TLS 1.3                                                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```
