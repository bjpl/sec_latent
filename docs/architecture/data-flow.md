# Data Flow Architecture

## Overview

This document details the end-to-end data flow through the SEC Filing Analysis System, from ingestion to final output.

## Processing Pipeline

### 1. Ingestion Phase

```
SEC EDGAR → Rate Limiter → Filing Fetcher → HTML Parser → Section Extractor → Metadata Store
```

**Steps**:

1. **Request Initiation**
   - Client provides CIK and filing type
   - System validates request parameters
   - Queue task for asynchronous processing

2. **SEC EDGAR Fetch**
   - Construct SEC EDGAR URL
   - Apply rate limiting (10 req/sec max)
   - Fetch filing metadata from index
   - Download HTML/XBRL content

3. **Content Parsing**
   - Detect filing format (HTML vs XBRL)
   - Parse document structure
   - Extract sections (MD&A, Risk Factors, etc.)
   - Identify tables and financial statements

4. **Metadata Storage**
   - Store filing metadata in Supabase
   - Cache parsed content for reuse
   - Generate document embeddings (ChromaDB)
   - Index for full-text search

**Data Format (Ingestion Output)**:
```json
{
  "filing_id": "uuid",
  "cik": "0000789019",
  "form_type": "10-K",
  "filing_date": "2024-02-06",
  "sections": {
    "mda": "text content...",
    "risk_factors": "text content...",
    "financial_statements": [...tables...]
  },
  "metadata": {
    "page_count": 85,
    "word_count": 45000,
    "table_count": 25
  }
}
```

### 2. Classification Phase

```
Filing Data → Complexity Assessor (Phi3) → Routing Decision → Queue Assignment
```

**Complexity Assessment Factors**:
- Document length (word count)
- Table density (tables per page)
- Financial statement complexity
- Footnote volume
- Historical filing comparison

**Routing Decision Tree**:
```
complexity_score < 0.4
  └─▶ Fast Track (Mistral 7B)

0.4 ≤ complexity_score < 0.7
  ├─▶ Hybrid (Mistral + DeepSeek)
  └─▶ Ensemble (5 models) [if high materiality]

complexity_score ≥ 0.7
  └─▶ Deep Analysis (DeepSeek-R1)
```

**Output**:
```json
{
  "complexity_score": 0.62,
  "recommended_route": "hybrid",
  "confidence": 0.93,
  "factors": {
    "text_length": 0.65,
    "table_density": 0.58,
    "materiality": 0.45
  }
}
```

### 3. Signal Extraction Phase

```
Routed Filing → Category Extractors (Parallel) → Signal Aggregation → Confidence Scoring
```

**Parallel Extraction**:

1. **Financial Signals** (Worker 1)
   - Revenue trends and growth
   - Margin analysis
   - Cash flow metrics
   - Balance sheet ratios
   - Working capital indicators

2. **Sentiment Signals** (Worker 2)
   - Forward-looking sentiment
   - Risk factor tone
   - Management optimism bias
   - MD&A consistency
   - Peer comparison sentiment

3. **Risk Signals** (Worker 3)
   - Risk factor analysis
   - Legal proceedings
   - Going concern indicators
   - Contingent liabilities
   - Material weaknesses

4. **Management Signals** (Worker 4)
   - Executive turnover
   - Compensation changes
   - Board composition
   - Related party transactions
   - Corporate governance metrics

**Signal Data Structure**:
```json
{
  "filing_id": "uuid",
  "signals": [
    {
      "category": "financial",
      "name": "revenue_growth_yoy",
      "value": 0.15,
      "confidence": 0.92,
      "metadata": {
        "prior_revenue": 100000000,
        "current_revenue": 115000000,
        "calculation_method": "direct"
      }
    },
    {
      "category": "sentiment",
      "name": "forward_looking_sentiment",
      "value": 0.68,
      "confidence": 0.87,
      "metadata": {
        "model": "finbert",
        "sentence_count": 45,
        "positive_ratio": 0.68
      }
    }
  ],
  "extraction_time_ms": 22000,
  "model_used": "mistral-7b"
}
```

### 4. Validation Phase

```
Signals → FACT Framework → GOALIE Protection → Metrics Tracking → Validated Output
```

**FACT Validation Layers**:

1. **Mathematical Layer** (Qwen2.5-coder)
   - Verify numerical calculations
   - Check unit consistency
   - Validate formulas
   - Detect statistical anomalies

2. **Logical Layer** (DeepSeek-R1)
   - Check reasoning consistency
   - Detect logical fallacies
   - Verify premise-conclusion validity
   - Identify contradictions

3. **Critical Layer** (Claude 3.5)
   - High-stakes decision review
   - External source verification
   - Regulatory compliance check
   - Expert-level validation

**GOALIE Protection**:

1. **Risk Assessment**
   - Categorize prediction type
   - Calculate base risk score
   - Identify risk factors
   - Assign risk level

2. **Confidence Scoring**
   - Extract model confidence scores
   - Calculate multi-model agreement
   - Compute variance metrics
   - Determine reliability

3. **Prediction Adjustment**
   - Apply conservative scaling
   - Add uncertainty ranges
   - Generate disclaimers
   - Filter by display threshold

**Validation Report**:
```json
{
  "filing_id": "uuid",
  "fact_validation": {
    "mathematical": {
      "passed": true,
      "confidence": 0.95,
      "checks": 25,
      "failures": 0
    },
    "logical": {
      "passed": true,
      "confidence": 0.89,
      "checks": 15,
      "failures": 1
    },
    "critical": {
      "passed": true,
      "confidence": 0.92,
      "checks": 10,
      "failures": 0
    }
  },
  "goalie_protection": {
    "risk_assessment": {
      "category": "financial_projection",
      "risk_level": "moderate",
      "risk_score": 0.45,
      "factors": ["forecast_uncertainty", "market_volatility"]
    },
    "confidence_score": {
      "aggregate": 0.88,
      "variance": 0.05,
      "reliability": "high"
    },
    "adjustment": {
      "factor": 0.95,
      "display": true,
      "disclaimer": "This is a model-based prediction..."
    }
  },
  "overall_passed": true,
  "risk_level": "moderate"
}
```

### 5. Aggregation Phase

```
Validated Signals → Result Aggregator → Response Formatter → API Response
```

**Aggregation Steps**:

1. **Collect Results**
   - Gather all signal values
   - Merge validation reports
   - Compile metadata
   - Calculate timing metrics

2. **Apply Business Logic**
   - Filter by confidence threshold
   - Apply display rules
   - Format numerical values
   - Add contextual information

3. **Format Response**
   - Convert to API schema
   - Add pagination support
   - Include metadata
   - Generate download links

**Final API Response**:
```json
{
  "filing_id": "uuid",
  "cik": "0000789019",
  "company_name": "Microsoft Corporation",
  "form_type": "10-K",
  "filing_date": "2024-02-06",
  "processing_summary": {
    "total_signals": 150,
    "passed_validation": 147,
    "confidence_avg": 0.89,
    "processing_time_ms": 22500,
    "model_used": "mistral-7b"
  },
  "signals": {
    "financial": [...50 signals...],
    "sentiment": [...30 signals...],
    "risk": [...40 signals...],
    "management": [...30 signals...]
  },
  "validation_summary": {
    "fact_passed": true,
    "goalie_risk_level": "moderate",
    "overall_confidence": 0.89
  },
  "links": {
    "raw_filing": "https://sec.gov/...",
    "detailed_report": "/api/reports/uuid",
    "download_csv": "/api/downloads/uuid.csv"
  }
}
```

## Data Storage Flow

### Write Path

```
API Request → Validation → Task Queue → Worker → Database Write → Cache Update
```

**Database Write Order**:
1. Filing metadata (Supabase)
2. Signal values (Supabase + DuckDB)
3. Validation reports (Supabase)
4. Embeddings (ChromaDB)
5. Cache updates (Redis)

### Read Path

```
API Request → Cache Check → Database Query → Result Formatting → Cache Update → Response
```

**Cache Strategy**:
- Check Redis cache first (TTL: 1 hour for hot data)
- Query Supabase for structured data
- Query DuckDB for analytics
- Query ChromaDB for semantic search
- Update cache on read (LRU eviction)

## Data Transformations

### 1. Raw Filing → Structured Data

```python
# Input: Raw HTML
<html>
  <body>
    <div>Management's Discussion and Analysis...</div>
  </body>
</html>

# Output: Structured sections
{
  "sections": {
    "mda": "Management's Discussion...",
    "risk_factors": "Risk Factors...",
    ...
  }
}
```

### 2. Text → Signals

```python
# Input: MD&A text
"Revenue increased 15% year-over-year from $100M to $115M..."

# Output: Financial signal
{
  "name": "revenue_growth_yoy",
  "value": 0.15,
  "confidence": 0.92
}
```

### 3. Signals → Validation Report

```python
# Input: Signal
{
  "name": "revenue_growth_yoy",
  "value": 0.15
}

# Output: Validated signal
{
  "name": "revenue_growth_yoy",
  "value": 0.15,
  "validated": true,
  "confidence": 0.92,
  "risk_level": "low"
}
```

## Error Handling Flow

### Retry Strategy

```
Task Failure → Error Classification → Retry Decision → Exponential Backoff → Retry or DLQ
```

**Error Types**:

1. **Transient Errors** (Retry)
   - Network timeouts
   - Rate limit exceeded
   - Temporary API unavailability
   - Database connection errors

2. **Permanent Errors** (No Retry)
   - Invalid CIK
   - Filing not found
   - Authentication failure
   - Validation schema error

3. **Retry Configuration**:
   - Max retries: 3
   - Initial delay: 2 seconds
   - Exponential backoff factor: 2
   - Max delay: 60 seconds

### Dead Letter Queue (DLQ)

```
Failed Task (after retries) → DLQ → Manual Review → Reprocess or Archive
```

## Performance Optimization

### Batch Processing

```
Multiple Filings → Batch Grouping → Parallel Workers → Result Aggregation
```

**Batch Strategy**:
- Group filings by complexity
- Assign to appropriate worker pools
- Process in parallel
- Aggregate results asynchronously

### Query Optimization

```
API Request → Query Optimizer → Cached Result or DB Query → Index Utilization
```

**Index Strategy**:
- Primary key indexes (filing_id)
- Secondary indexes (cik, filing_date)
- Composite indexes (cik, form_type, filing_date)
- Full-text indexes (section content)

## Monitoring Data Flow

### Metrics Collection

```
Operation → Metric Emission → Prometheus → Grafana Dashboard
```

**Key Metrics**:
- Ingestion rate (filings/hour)
- Signal extraction latency
- Validation pass rate
- Model inference time
- Cache hit rate
- Error rate by type

### Logging Flow

```
Operation → Structured Log → Log Aggregator → Search/Alert
```

**Log Levels**:
- DEBUG: Detailed execution traces
- INFO: Normal operations
- WARNING: Degraded performance
- ERROR: Operation failures
- CRITICAL: System failures

---

**Document Version**: 1.0
**Last Updated**: 2025-10-18
**Owner**: Architecture Team
**Review Cycle**: Quarterly
