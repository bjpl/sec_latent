# Developer Onboarding Guide

Welcome to the SEC Latent Signal Analysis Platform development team! This guide will help you get up and running quickly.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Architecture Overview](#architecture-overview)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Code Review](#code-review)
- [Deployment](#deployment)
- [Resources](#resources)

## Prerequisites

### Required Knowledge

- **Python 3.11+**: Advanced proficiency required
- **FastAPI**: RESTful API development
- **Celery**: Distributed task queue experience
- **Docker & Kubernetes**: Container orchestration
- **PostgreSQL**: Database design and optimization
- **Git**: Version control and collaboration

### Software Requirements

```bash
# Development tools
python >= 3.11
docker >= 24.0
docker-compose >= 2.20
kubectl >= 1.28
git >= 2.40

# Python tools
pip >= 23.0
poetry >= 1.5.0  # Optional, for dependency management
pre-commit >= 3.3.0

# Recommended IDEs
VSCode with Python extension
PyCharm Professional
```

### System Requirements

- **OS**: Linux, macOS, or WSL2 (Windows)
- **RAM**: 16GB minimum, 32GB recommended
- **Storage**: 50GB free space
- **GPU**: Optional, but recommended for model inference

## Environment Setup

### 1. Clone Repository

```bash
# SSH (recommended)
git clone git@github.com:your-org/sec-latent.git

# HTTPS
git clone https://github.com/your-org/sec-latent.git

cd sec-latent
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### 3. Configure Environment Variables

```bash
# Copy environment template
cp config/.env.example .env

# Edit .env with your credentials
# IMPORTANT: Never commit .env file
nano .env
```

**Required Environment Variables:**

```bash
# Database (Supabase)
DATABASE_URL=postgresql://user:pass@host:5432/sec_latent
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# Redis
REDIS_URL=redis://localhost:6379/0

# API Keys
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Security
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=RS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15

# Application
ENVIRONMENT=development
LOG_LEVEL=DEBUG
API_HOST=0.0.0.0
API_PORT=8000

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_WORKER_CONCURRENCY=4
```

### 4. Start Local Services

```bash
# Start all services with Docker Compose
docker-compose up -d

# Verify services are running
docker-compose ps

# Check service logs
docker-compose logs -f api
docker-compose logs -f worker
```

**Services Started:**
- **API Server**: http://localhost:8000
- **Redis**: localhost:6379
- **PostgreSQL**: localhost:5432 (via Supabase)
- **Celery Worker**: Background processing
- **Celery Flower**: http://localhost:5555 (task monitoring)

### 5. Initialize Database

```bash
# Apply database migrations
python scripts/migrate.py

# Load seed data (optional)
python scripts/seed_data.py

# Verify database connection
python -c "from src.data.database_connectors import SupabaseConnector; print(SupabaseConnector().test_connection())"
```

### 6. Verify Installation

```bash
# Health check
curl http://localhost:8000/health

# Expected response:
# {
#   "status": "healthy",
#   "version": "1.0.0",
#   "services": {
#     "api": {"status": "healthy"},
#     "database": {"status": "healthy"},
#     "task_queue": {"status": "healthy"}
#   }
# }

# Run test suite
pytest tests/ -v

# Expected: All tests pass with >80% coverage
```

## Architecture Overview

### System Components

```
┌──────────────────────────────────────────────┐
│           SEC Latent Signal Platform          │
├──────────────────────────────────────────────┤
│                                               │
│  ┌───────────┐    ┌───────────┐             │
│  │  FastAPI  │───▶│  Celery   │             │
│  │    API    │    │  Workers  │             │
│  └─────┬─────┘    └─────┬─────┘             │
│        │                 │                   │
│        ▼                 ▼                   │
│  ┌──────────────────────────────┐           │
│  │        Redis Queue            │           │
│  └──────────────────────────────┘           │
│        │                                     │
│        ▼                                     │
│  ┌───────────┐  ┌─────────┐  ┌──────────┐  │
│  │ Supabase  │  │ DuckDB  │  │ ChromaDB │  │
│  │(Postgres) │  │(Analytics)│  │(Vectors) │  │
│  └───────────┘  └─────────┘  └──────────┘  │
└──────────────────────────────────────────────┘
```

### Directory Structure

```
src/
├── api/                    # FastAPI application
│   ├── main.py             # Application entry point
│   ├── routes/             # API route handlers
│   ├── middleware/         # Custom middleware
│   └── dependencies.py     # Dependency injection
│
├── data/                   # Data layer
│   ├── sec_edgar_connector.py    # SEC EDGAR API client
│   ├── database_connectors.py    # Database connections
│   └── parsers/            # Filing parsers
│
├── models/                 # Model layer
│   ├── model_router.py     # Intelligent routing
│   ├── inference.py        # Model inference
│   └── ensemble.py         # Ensemble strategies
│
├── signals/                # Signal extraction
│   ├── signal_extractor.py       # Base extractor
│   ├── financial_signals.py      # Financial signals
│   ├── sentiment_signals.py      # Sentiment signals
│   ├── risk_signals.py           # Risk signals
│   └── management_signals.py     # Management signals
│
├── validation/             # Validation frameworks
│   ├── fact.py             # FACT framework
│   ├── goalie.py           # GOALIE protection
│   └── metrics.py          # Quality metrics
│
├── pipeline/               # Task orchestration
│   ├── celery_tasks.py     # Celery task definitions
│   └── workflows.py        # Task workflows
│
└── utils/                  # Utilities
    ├── logging.py          # Structured logging
    ├── cache.py            # Caching utilities
    └── monitoring.py       # Metrics collection
```

### Key Design Patterns

1. **Dependency Injection**: FastAPI dependency system for testability
2. **Repository Pattern**: Data access layer abstraction
3. **Strategy Pattern**: Model routing and validation strategies
4. **Observer Pattern**: Event-driven processing
5. **Circuit Breaker**: Fault tolerance for external services

## Development Workflow

### 1. Feature Development

```bash
# 1. Create feature branch
git checkout -b feature/signal-extraction-enhancement

# 2. Make changes
# Edit files, write tests, update documentation

# 3. Run tests locally
pytest tests/ -v
pytest --cov=src tests/

# 4. Check code quality
# Pre-commit hooks run automatically on commit
git add .
git commit -m "feat: enhance financial signal extraction"

# 5. Push branch
git push origin feature/signal-extraction-enhancement

# 6. Create pull request
# Use GitHub UI to create PR with description
```

### 2. Coding Standards

**Python Style:**
```python
# Use Black for formatting (120 character line limit)
# Use type hints for all function signatures
# Use Google-style docstrings

def extract_signals(
    filing_id: str,
    categories: list[str],
    confidence_threshold: float = 0.7
) -> list[Signal]:
    """Extract signals from a filing.

    Args:
        filing_id: Unique filing identifier
        categories: List of signal categories to extract
        confidence_threshold: Minimum confidence score (0.0-1.0)

    Returns:
        List of extracted signals with confidence scores

    Raises:
        ValueError: If filing_id is invalid
        ExtractionError: If extraction fails
    """
    # Implementation
    pass
```

**Error Handling:**
```python
from src.utils.exceptions import ExtractionError, ValidationError

try:
    signals = extractor.extract(filing_id)
except ExtractionError as e:
    logger.error(f"Extraction failed: {e}", extra={"filing_id": filing_id})
    raise
except Exception as e:
    logger.exception(f"Unexpected error: {e}")
    raise ExtractionError(f"Failed to extract signals: {e}") from e
```

**Logging:**
```python
import logging
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Structured logging with context
logger.info(
    "Signal extraction started",
    extra={
        "filing_id": filing_id,
        "categories": categories,
        "user_id": user_id
    }
)
```

### 3. Testing

**Unit Tests:**
```python
# tests/unit/signals/test_financial_signals.py

import pytest
from src.signals.financial_signals import FinancialSignalExtractor

@pytest.fixture
def extractor():
    return FinancialSignalExtractor()

@pytest.fixture
def sample_filing():
    return {
        "cik": "0000789019",
        "form_type": "10-K",
        "sections": {
            "financial_statements": "Revenue: $150M..."
        }
    }

def test_revenue_extraction(extractor, sample_filing):
    """Test revenue signal extraction."""
    signals = extractor.extract(sample_filing)

    revenue_signal = next(s for s in signals if s.name == "revenue")

    assert revenue_signal.value == 150_000_000
    assert revenue_signal.confidence > 0.8
    assert revenue_signal.category == "financial"

def test_invalid_filing_raises_error(extractor):
    """Test error handling for invalid filing."""
    with pytest.raises(ValueError, match="Invalid filing"):
        extractor.extract(None)
```

**Integration Tests:**
```python
# tests/integration/test_filing_pipeline.py

import pytest
from src.pipeline.workflows import FilingPipeline

@pytest.mark.integration
@pytest.mark.asyncio
async def test_end_to_end_pipeline(test_client, test_db):
    """Test complete filing processing pipeline."""
    # Create test filing
    filing_id = await test_db.create_filing(
        cik="0000789019",
        form_type="10-K"
    )

    # Process filing
    pipeline = FilingPipeline()
    result = await pipeline.process(filing_id)

    # Assertions
    assert result.status == "completed"
    assert result.signal_count == 150
    assert result.validation_passed is True

    # Cleanup
    await test_db.delete_filing(filing_id)
```

**Running Tests:**
```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/unit/signals/test_financial_signals.py -v

# Test with coverage
pytest --cov=src --cov-report=html tests/

# Open coverage report
open htmlcov/index.html

# Integration tests only
pytest -m integration tests/

# Security tests
pytest tests/security/ -v
```

### 4. Debugging

**Local Debugging:**
```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or use built-in breakpoint()
breakpoint()

# Common pdb commands:
# l (list) - show code context
# n (next) - execute next line
# s (step) - step into function
# c (continue) - continue execution
# p var - print variable
# q (quit) - exit debugger
```

**Remote Debugging (in Docker):**
```python
# Install debugpy
pip install debugpy

# Add to code
import debugpy
debugpy.listen(("0.0.0.0", 5678))
debugpy.wait_for_client()

# Expose port in docker-compose.yml
ports:
  - "5678:5678"

# Connect from VSCode with launch.json
```

## Code Review

### PR Requirements

- [ ] All tests pass
- [ ] Coverage > 80%
- [ ] Security scan passed (no critical/high findings)
- [ ] Documentation updated
- [ ] Code follows style guide
- [ ] No merge conflicts
- [ ] Commit messages follow convention
- [ ] PR description includes context and testing notes

### Review Process

1. **Self-Review**: Review your own changes first
2. **Automated Checks**: Wait for CI/CD pipeline
3. **Peer Review**: Request 2+ reviewers
4. **Address Feedback**: Respond to all comments
5. **Final Approval**: Get approval from all reviewers
6. **Merge**: Squash and merge to main

### Common Review Comments

- "Add type hints to function signature"
- "Extract magic number to constant"
- "Add error handling for edge case"
- "Update docstring with new parameter"
- "Consider using context manager"

## Deployment

### Development Deployment

```bash
# Deploy to development environment
docker-compose up -d --build

# Verify deployment
curl http://localhost:8000/health
```

### Staging Deployment

```bash
# Deploy to staging
kubectl apply -k k8s/overlays/staging

# Check deployment status
kubectl rollout status deployment/api -n staging

# View logs
kubectl logs -f deployment/api -n staging
```

### Production Deployment

**Automated Deployment (via CI/CD):**
- Merge to `main` branch triggers production deployment
- Automated tests run first
- Security scans must pass
- Manual approval required for production
- Automated rollback on failure

**Manual Deployment (emergency only):**
```bash
# Deploy to production
kubectl apply -k k8s/overlays/prod

# Monitor deployment
kubectl rollout status deployment/api -n prod

# Rollback if needed
kubectl rollout undo deployment/api -n prod
```

## Resources

### Documentation

- **System Architecture**: [docs/architecture/system-design.md](../architecture/system-design.md)
- **API Documentation**: [docs/api/rest-api.md](../api/rest-api.md)
- **Operations Runbook**: [docs/operations/runbook.md](../operations/runbook.md)

### Internal Resources

- **Team Wiki**: https://wiki.internal/sec-latent
- **Slack Channels**:
  - #sec-latent-dev (development)
  - #sec-latent-alerts (alerts)
  - #sec-latent-deploy (deployments)
- **Jira Board**: https://jira.internal/sec-latent
- **Design Docs**: https://drive.internal/sec-latent

### External Resources

- **FastAPI**: https://fastapi.tiangolo.com/
- **Celery**: https://docs.celeryproject.org/
- **PostgreSQL**: https://www.postgresql.org/docs/
- **Kubernetes**: https://kubernetes.io/docs/

### Getting Help

- **Questions**: Ask in #sec-latent-dev Slack channel
- **Issues**: Create GitHub issue with [BUG] or [QUESTION] prefix
- **On-Call**: PagerDuty rotation for production issues
- **Office Hours**: Thursday 2-3 PM for Q&A

---

**Welcome aboard! 🚀**

If you have any questions, don't hesitate to reach out to the team.

**Document Version**: 1.0
**Last Updated**: 2025-10-18
**Owner**: Engineering Team
