# REST API Reference

## Overview

The SEC Filing Analysis System provides a comprehensive REST API for accessing filing data, extracting signals, and managing validation operations.

**Base URL**: `https://api.sec-analysis.com/v1`

**Authentication**: Bearer token (JWT)

## Authentication

### Obtain Access Token

```http
POST /auth/token
Content-Type: application/json

{
  "client_id": "your_client_id",
  "client_secret": "your_client_secret"
}
```

**Response**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

### Using Access Token

```http
GET /filings
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

## Endpoints

### Filings

#### GET /filings

Retrieve list of filings.

**Parameters**:
- `cik` (optional): Company CIK
- `form_type` (optional): Filing type (10-K, 10-Q, 8-K)
- `from_date` (optional): Start date (YYYY-MM-DD)
- `to_date` (optional): End date (YYYY-MM-DD)
- `limit` (optional): Results per page (default: 20, max: 100)
- `offset` (optional): Pagination offset (default: 0)

**Example Request**:
```http
GET /filings?cik=0000789019&form_type=10-K&limit=10
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Response** (200 OK):
```json
{
  "count": 45,
  "next": "/filings?offset=10",
  "previous": null,
  "results": [
    {
      "filing_id": "550e8400-e29b-41d4-a716-446655440000",
      "cik": "0000789019",
      "company_name": "Microsoft Corporation",
      "form_type": "10-K",
      "filing_date": "2024-02-06",
      "fiscal_year_end": "2024-06-30",
      "status": "processed",
      "signal_count": 150,
      "links": {
        "self": "/filings/550e8400-e29b-41d4-a716-446655440000",
        "signals": "/filings/550e8400-e29b-41d4-a716-446655440000/signals",
        "raw": "https://www.sec.gov/..."
      }
    }
  ]
}
```

#### GET /filings/{filing_id}

Retrieve specific filing details.

**Example Request**:
```http
GET /filings/550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Response** (200 OK):
```json
{
  "filing_id": "550e8400-e29b-41d4-a716-446655440000",
  "cik": "0000789019",
  "company_name": "Microsoft Corporation",
  "form_type": "10-K",
  "filing_date": "2024-02-06",
  "fiscal_year_end": "2024-06-30",
  "accession_number": "0001564590-24-000123",
  "status": "processed",
  "processing_summary": {
    "started_at": "2024-02-06T10:00:00Z",
    "completed_at": "2024-02-06T10:00:23Z",
    "duration_ms": 23000,
    "model_used": "mistral-7b",
    "complexity_score": 0.42
  },
  "sections": {
    "mda": {
      "word_count": 12500,
      "extracted": true
    },
    "risk_factors": {
      "word_count": 8300,
      "extracted": true
    },
    "financial_statements": {
      "table_count": 25,
      "extracted": true
    }
  },
  "links": {
    "signals": "/filings/550e8400-e29b-41d4-a716-446655440000/signals",
    "validation": "/filings/550e8400-e29b-41d4-a716-446655440000/validation",
    "raw": "https://www.sec.gov/..."
  }
}
```

#### POST /filings/process

Queue filing for processing.

**Request Body**:
```json
{
  "cik": "0000789019",
  "form_type": "10-K",
  "filing_date": "2024-02-06",
  "priority": "high",
  "options": {
    "extract_signals": true,
    "run_validation": true,
    "generate_embeddings": true
  }
}
```

**Response** (202 Accepted):
```json
{
  "task_id": "abc123def456",
  "status": "queued",
  "estimated_completion": "2024-02-06T10:01:00Z",
  "links": {
    "status": "/tasks/abc123def456",
    "cancel": "/tasks/abc123def456/cancel"
  }
}
```

### Signals

#### GET /filings/{filing_id}/signals

Retrieve all signals for a filing.

**Parameters**:
- `category` (optional): Filter by category (financial, sentiment, risk, management)
- `min_confidence` (optional): Minimum confidence threshold (0.0-1.0)
- `format` (optional): Response format (json, csv) (default: json)

**Example Request**:
```http
GET /filings/550e8400-e29b-41d4-a716-446655440000/signals?category=financial&min_confidence=0.8
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Response** (200 OK):
```json
{
  "filing_id": "550e8400-e29b-41d4-a716-446655440000",
  "signal_count": 50,
  "categories": {
    "financial": 50,
    "sentiment": 0,
    "risk": 0,
    "management": 0
  },
  "signals": [
    {
      "signal_id": "sig_001",
      "name": "revenue_growth_yoy",
      "category": "financial",
      "value": 0.15,
      "confidence": 0.92,
      "metadata": {
        "prior_revenue": 100000000,
        "current_revenue": 115000000,
        "calculation_method": "direct",
        "source_section": "income_statement"
      },
      "validation": {
        "fact_passed": true,
        "goalie_risk_level": "low"
      }
    }
  ],
  "extraction_summary": {
    "model_used": "mistral-7b",
    "extraction_time_ms": 5200,
    "avg_confidence": 0.89
  }
}
```

#### POST /signals/extract

Extract signals from custom text.

**Request Body**:
```json
{
  "text": "Revenue increased 15% year-over-year...",
  "context": {
    "company_name": "Example Corp",
    "fiscal_year": 2024
  },
  "categories": ["financial", "sentiment"],
  "options": {
    "run_validation": true,
    "min_confidence": 0.7
  }
}
```

**Response** (200 OK):
```json
{
  "signals": [...],
  "processing_time_ms": 3500,
  "model_used": "mistral-7b"
}
```

### Validation

#### POST /validate

Validate claims or predictions.

**Request Body**:
```json
{
  "claim": "Revenue will increase by 20% next quarter",
  "context": {
    "company_cik": "0000789019",
    "historical_data": {...}
  },
  "validation_types": ["mathematical", "logical", "critical"],
  "protection_options": {
    "apply_goalie": true,
    "risk_threshold": "moderate"
  }
}
```

**Response** (200 OK):
```json
{
  "validation_id": "val_123",
  "overall_passed": true,
  "confidence_score": 0.88,
  "risk_level": "moderate",
  "fact_validation": {
    "mathematical": {
      "passed": true,
      "confidence": 0.95,
      "checks_run": 25
    },
    "logical": {
      "passed": true,
      "confidence": 0.89,
      "checks_run": 15
    },
    "critical": {
      "passed": true,
      "confidence": 0.92,
      "checks_run": 10
    }
  },
  "goalie_protection": {
    "risk_assessment": {
      "category": "financial_projection",
      "risk_level": "moderate",
      "risk_score": 0.45
    },
    "adjusted_prediction": {
      "original": 0.20,
      "adjusted": 0.19,
      "adjustment_factor": 0.95,
      "display": true
    }
  },
  "recommendations": [
    "Consider adding uncertainty ranges",
    "Monitor market conditions"
  ]
}
```

### Tasks

#### GET /tasks/{task_id}

Check task status.

**Example Request**:
```http
GET /tasks/abc123def456
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Response** (200 OK):
```json
{
  "task_id": "abc123def456",
  "status": "processing",
  "progress": 65,
  "created_at": "2024-02-06T10:00:00Z",
  "updated_at": "2024-02-06T10:00:15Z",
  "estimated_completion": "2024-02-06T10:00:23Z",
  "result": null,
  "error": null
}
```

**Status Values**:
- `queued`: Task is waiting in queue
- `processing`: Task is being processed
- `completed`: Task completed successfully
- `failed`: Task failed with error

#### DELETE /tasks/{task_id}

Cancel a queued or processing task.

**Response** (200 OK):
```json
{
  "task_id": "abc123def456",
  "status": "cancelled",
  "message": "Task cancelled successfully"
}
```

### Health & Metrics

#### GET /health

System health check.

**Response** (200 OK):
```json
{
  "status": "healthy",
  "timestamp": "2024-02-06T10:00:00Z",
  "version": "1.0.0",
  "services": {
    "api": {
      "status": "healthy",
      "latency_ms": 15
    },
    "database": {
      "status": "healthy",
      "connection_pool": {
        "active": 5,
        "idle": 15,
        "max": 20
      }
    },
    "task_queue": {
      "status": "healthy",
      "pending_tasks": 23,
      "active_workers": 4
    }
  }
}
```

#### GET /metrics

Prometheus metrics endpoint.

**Response** (200 OK - Prometheus format):
```
# HELP api_requests_total Total API requests
# TYPE api_requests_total counter
api_requests_total{method="GET",endpoint="/filings",status="200"} 1543

# HELP api_request_duration_seconds API request duration
# TYPE api_request_duration_seconds histogram
api_request_duration_seconds_bucket{le="0.1"} 1234
api_request_duration_seconds_bucket{le="0.5"} 1500
api_request_duration_seconds_bucket{le="1.0"} 1543
```

## Error Responses

### 400 Bad Request

Invalid request parameters.

```json
{
  "error": "bad_request",
  "message": "Invalid CIK format",
  "details": {
    "field": "cik",
    "reason": "Must be 10 digits"
  }
}
```

### 401 Unauthorized

Missing or invalid authentication.

```json
{
  "error": "unauthorized",
  "message": "Invalid or expired token"
}
```

### 403 Forbidden

Insufficient permissions.

```json
{
  "error": "forbidden",
  "message": "Insufficient permissions for this operation"
}
```

### 404 Not Found

Resource not found.

```json
{
  "error": "not_found",
  "message": "Filing not found",
  "filing_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 429 Too Many Requests

Rate limit exceeded.

```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests",
  "retry_after": 60
}
```

### 500 Internal Server Error

Server error.

```json
{
  "error": "internal_server_error",
  "message": "An unexpected error occurred",
  "request_id": "req_123456"
}
```

## Rate Limiting

**Limits**:
- Standard tier: 100 requests/minute
- Premium tier: 1000 requests/minute
- Enterprise tier: Custom limits

**Headers**:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 85
X-RateLimit-Reset: 1707217260
```

## Pagination

Use `limit` and `offset` parameters:

```http
GET /filings?limit=20&offset=40
```

**Response includes pagination links**:
```json
{
  "count": 150,
  "next": "/filings?limit=20&offset=60",
  "previous": "/filings?limit=20&offset=20",
  "results": [...]
}
```

## Filtering & Sorting

**Filtering**:
```http
GET /filings?cik=0000789019&form_type=10-K&from_date=2023-01-01
```

**Sorting**:
```http
GET /filings?sort=-filing_date  # Descending
GET /filings?sort=filing_date   # Ascending
```

## Webhooks

Register webhook endpoints to receive notifications:

```http
POST /webhooks
Content-Type: application/json

{
  "url": "https://your-app.com/webhook",
  "events": ["filing.processed", "task.completed"],
  "secret": "your_webhook_secret"
}
```

**Webhook Payload**:
```json
{
  "event": "filing.processed",
  "timestamp": "2024-02-06T10:00:23Z",
  "data": {
    "filing_id": "550e8400-e29b-41d4-a716-446655440000",
    "cik": "0000789019",
    "status": "completed"
  },
  "signature": "sha256=..."
}
```

## SDK Examples

### Python

```python
from sec_analysis import Client

client = Client(api_key="your_api_key")

# Fetch filings
filings = client.filings.list(cik="0000789019", form_type="10-K")

# Extract signals
filing = filings[0]
signals = client.signals.extract(filing.id)

# Run validation
result = client.validate(
    claim="Revenue will increase by 20%",
    context={"company": "MSFT"}
)
```

### cURL

```bash
# Fetch filings
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.sec-analysis.com/v1/filings?cik=0000789019"

# Process filing
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"cik": "0000789019", "form_type": "10-K"}' \
  "https://api.sec-analysis.com/v1/filings/process"
```

---

**Document Version**: 1.0
**Last Updated**: 2025-10-18
**Owner**: API Team
**Review Cycle**: Monthly
