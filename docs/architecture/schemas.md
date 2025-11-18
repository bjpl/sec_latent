# Database Schema Design
**SEC Filing Analysis System - Data Infrastructure Architecture**

## Schema Overview

This document defines the complete database schemas for persistent storage (Supabase PostgreSQL), analytical queries (DuckDB), and caching (Redis). The architecture supports 100+ filings/hour processing with 99.9% reliability and sub-100ms query performance for hot data.

---

## 1. SUPABASE (CLOUD POSTGRESQL) - PERSISTENT STORAGE

### 1.1 Core Tables

#### `filings` (Primary Filing Repository)
```sql
CREATE TABLE filings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cik VARCHAR(10) NOT NULL,
    company_name VARCHAR(255),
    ticker VARCHAR(10),
    form_type VARCHAR(10) NOT NULL,
    filing_date DATE NOT NULL,
    fiscal_year INTEGER,
    fiscal_quarter INTEGER,
    accession_number VARCHAR(25) UNIQUE NOT NULL,
    document_url TEXT NOT NULL,
    file_number VARCHAR(20),

    -- Processing metadata
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processing_duration_ms INTEGER,
    model_used VARCHAR(50),
    pipeline_version VARCHAR(20),

    -- Signal counts
    signal_count INTEGER DEFAULT 0,
    linguistic_signals INTEGER DEFAULT 0,
    structural_signals INTEGER DEFAULT 0,
    network_signals INTEGER DEFAULT 0,
    temporal_signals INTEGER DEFAULT 0,
    visual_signals INTEGER DEFAULT 0,

    -- Quality metrics
    confidence_score DECIMAL(5,4),
    quality_score DECIMAL(5,4),
    completeness_score DECIMAL(5,4),

    -- Document statistics
    document_length INTEGER,
    section_count INTEGER,
    table_count INTEGER,
    chart_count INTEGER,

    -- Indexes
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT filings_cik_fk FOREIGN KEY (cik) REFERENCES companies(cik),
    INDEX idx_filings_cik (cik),
    INDEX idx_filings_form_type (form_type),
    INDEX idx_filings_filing_date (filing_date),
    INDEX idx_filings_accession (accession_number),
    INDEX idx_filings_processed_at (processed_at),
    INDEX idx_filings_company_date (cik, filing_date DESC)
);

-- Partitioning by filing_date for performance
CREATE TABLE filings_2025_q1 PARTITION OF filings
    FOR VALUES FROM ('2025-01-01') TO ('2025-04-01');
CREATE TABLE filings_2025_q2 PARTITION OF filings
    FOR VALUES FROM ('2025-04-01') TO ('2025-07-01');
-- Additional quarterly partitions...

-- Row-level security
ALTER TABLE filings ENABLE ROW LEVEL SECURITY;
CREATE POLICY filings_read_policy ON filings
    FOR SELECT USING (true);
```

#### `companies` (Company Master Data)
```sql
CREATE TABLE companies (
    cik VARCHAR(10) PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    ticker VARCHAR(10),
    exchange VARCHAR(10),
    sic_code VARCHAR(4),
    sic_description VARCHAR(255),
    naics_code VARCHAR(6),
    naics_description VARCHAR(255),

    -- Corporate information
    state_of_incorporation VARCHAR(2),
    fiscal_year_end VARCHAR(4),
    business_address JSONB,
    mailing_address JSONB,

    -- Metadata
    irs_number VARCHAR(10),
    former_names JSONB,

    -- Statistics
    total_filings INTEGER DEFAULT 0,
    first_filing_date DATE,
    last_filing_date DATE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    INDEX idx_companies_ticker (ticker),
    INDEX idx_companies_sic (sic_code),
    INDEX idx_companies_naics (naics_code)
);
```

#### `signals` (Extracted Signals Repository)
```sql
CREATE TABLE signals (
    id BIGSERIAL PRIMARY KEY,
    filing_id UUID NOT NULL,

    -- Signal identification
    signal_code VARCHAR(10) NOT NULL, -- e.g., "L001", "S015", "N042"
    signal_name VARCHAR(100) NOT NULL,
    signal_category VARCHAR(20) NOT NULL, -- linguistic/structural/network/temporal/visual
    signal_dimension VARCHAR(50), -- sentiment_tone/complexity/entity_relationships/etc

    -- Signal value and metadata
    signal_value JSONB NOT NULL, -- Flexible storage for different value types
    confidence DECIMAL(5,4) DEFAULT 1.0,
    quality_score DECIMAL(5,4),

    -- Context
    section_source VARCHAR(50), -- MD&A, Risk Factors, etc.
    extraction_method VARCHAR(50), -- bert_sentiment, regex_pattern, etc.

    -- Validation
    is_validated BOOLEAN DEFAULT FALSE,
    validation_method VARCHAR(50),
    validation_score DECIMAL(5,4),

    -- Research backing
    research_citation TEXT,
    expected_range_min DECIMAL(10,4),
    expected_range_max DECIMAL(10,4),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT signals_filing_fk FOREIGN KEY (filing_id) REFERENCES filings(id) ON DELETE CASCADE,
    INDEX idx_signals_filing (filing_id),
    INDEX idx_signals_code (signal_code),
    INDEX idx_signals_category (signal_category),
    INDEX idx_signals_name (signal_name),
    INDEX idx_signals_confidence (confidence),
    INDEX idx_signals_composite (filing_id, signal_category, confidence)
);

-- Partitioning by signal_category for query optimization
CREATE TABLE signals_linguistic PARTITION OF signals
    FOR VALUES IN ('linguistic');
CREATE TABLE signals_structural PARTITION OF signals
    FOR VALUES IN ('structural');
-- Additional category partitions...
```

#### `signal_definitions` (Signal Taxonomy Reference)
```sql
CREATE TABLE signal_definitions (
    signal_code VARCHAR(10) PRIMARY KEY,
    signal_name VARCHAR(100) NOT NULL,
    category VARCHAR(20) NOT NULL,
    dimension VARCHAR(50) NOT NULL,

    -- Documentation
    description TEXT NOT NULL,
    extraction_method TEXT,
    expected_range VARCHAR(50),
    value_type VARCHAR(20), -- numeric/boolean/categorical/json

    -- Research foundation
    research_paper TEXT,
    research_year INTEGER,
    research_citation TEXT,

    -- Validation criteria
    statistical_significance_threshold DECIMAL(5,4),
    min_correlation DECIMAL(5,4),

    -- Computational requirements
    extraction_complexity VARCHAR(20), -- low/medium/high
    avg_extraction_time_ms INTEGER,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    version VARCHAR(10),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    INDEX idx_signal_defs_category (category),
    INDEX idx_signal_defs_active (is_active)
);
```

#### `analyses` (AI Model Analysis Results)
```sql
CREATE TABLE analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filing_id UUID NOT NULL,

    -- Model information
    model_tier VARCHAR(10) NOT NULL, -- tier1/tier2a/tier2b/tier2c/tier2d
    model_name VARCHAR(50) NOT NULL,
    model_version VARCHAR(20),

    -- Processing metadata
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,

    -- Analysis outputs
    summary TEXT,
    key_findings JSONB,
    risk_assessment JSONB,
    financial_metrics JSONB,
    governance_analysis JSONB,
    forward_looking_statements JSONB,

    -- Quality metrics
    confidence_score DECIMAL(5,4),
    completeness_score DECIMAL(5,4),
    consistency_score DECIMAL(5,4),

    -- Token usage (for cost tracking)
    input_tokens INTEGER,
    output_tokens INTEGER,

    -- Ensemble metadata (for tier2c)
    is_ensemble BOOLEAN DEFAULT FALSE,
    ensemble_agreement_rate DECIMAL(5,4),
    participating_models JSONB,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT analyses_filing_fk FOREIGN KEY (filing_id) REFERENCES filings(id) ON DELETE CASCADE,
    INDEX idx_analyses_filing (filing_id),
    INDEX idx_analyses_model (model_tier, model_name),
    INDEX idx_analyses_completed (completed_at),
    INDEX idx_analyses_confidence (confidence_score)
);
```

### 1.2 Relationship & Network Tables

#### `entities` (Officers, Directors, Subsidiaries)
```sql
CREATE TABLE entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type VARCHAR(20) NOT NULL, -- officer/director/subsidiary/auditor/counsel

    -- Identification
    name VARCHAR(255) NOT NULL,
    normalized_name VARCHAR(255), -- For matching
    external_id VARCHAR(50), -- CIK, EIN, etc.

    -- Person-specific fields
    title VARCHAR(100),
    age INTEGER,
    education JSONB,
    prior_companies JSONB,

    -- Organization-specific fields
    address JSONB,
    state_of_incorporation VARCHAR(2),

    -- Statistics
    first_seen DATE,
    last_seen DATE,
    mention_count INTEGER DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    INDEX idx_entities_type (entity_type),
    INDEX idx_entities_name (name),
    INDEX idx_entities_normalized (normalized_name)
);
```

#### `entity_relationships` (Network Connections)
```sql
CREATE TABLE entity_relationships (
    id BIGSERIAL PRIMARY KEY,
    filing_id UUID NOT NULL,

    -- Relationship
    source_entity_id UUID NOT NULL,
    target_entity_id UUID,
    target_company_cik VARCHAR(10),

    relationship_type VARCHAR(50) NOT NULL, -- employment/board_membership/ownership/audit/legal
    relationship_details JSONB,

    -- Temporal
    effective_date DATE,
    end_date DATE,
    is_current BOOLEAN DEFAULT TRUE,

    -- Network metrics
    strength DECIMAL(5,4), -- Relationship strength indicator
    centrality_score DECIMAL(10,8),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT entity_rel_filing_fk FOREIGN KEY (filing_id) REFERENCES filings(id) ON DELETE CASCADE,
    CONSTRAINT entity_rel_source_fk FOREIGN KEY (source_entity_id) REFERENCES entities(id),
    CONSTRAINT entity_rel_target_fk FOREIGN KEY (target_entity_id) REFERENCES entities(id),
    INDEX idx_entity_rel_filing (filing_id),
    INDEX idx_entity_rel_source (source_entity_id),
    INDEX idx_entity_rel_target (target_entity_id),
    INDEX idx_entity_rel_type (relationship_type)
);
```

### 1.3 Temporal & History Tables

#### `filing_comparisons` (Year-over-Year Changes)
```sql
CREATE TABLE filing_comparisons (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    current_filing_id UUID NOT NULL,
    prior_filing_id UUID NOT NULL,

    -- Change metrics
    document_length_change_pct DECIMAL(8,4),
    section_length_changes JSONB, -- Section-by-section changes

    -- Signal changes
    signal_changes JSONB, -- Signal code -> delta mapping
    significant_changes JSONB, -- Flagged important changes

    -- Semantic similarity
    overall_similarity DECIMAL(5,4),
    section_similarities JSONB,

    -- Detected anomalies
    anomalies JSONB,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT filing_comp_current_fk FOREIGN KEY (current_filing_id) REFERENCES filings(id),
    CONSTRAINT filing_comp_prior_fk FOREIGN KEY (prior_filing_id) REFERENCES filings(id),
    INDEX idx_filing_comp_current (current_filing_id)
);
```

#### `time_series_metrics` (Historical Trends)
```sql
CREATE TABLE time_series_metrics (
    id BIGSERIAL PRIMARY KEY,
    cik VARCHAR(10) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,

    -- Time series data
    date_values JSONB NOT NULL, -- Array of {date, value} objects

    -- Statistical analysis
    trend_direction VARCHAR(10), -- increasing/decreasing/stable
    slope DECIMAL(10,6),
    r_squared DECIMAL(5,4),

    -- Seasonality
    has_seasonality BOOLEAN DEFAULT FALSE,
    seasonal_period INTEGER,
    seasonal_strength DECIMAL(5,4),

    -- Forecast
    forecast_values JSONB,
    forecast_confidence JSONB,

    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT timeseries_company_fk FOREIGN KEY (cik) REFERENCES companies(cik),
    INDEX idx_timeseries_cik (cik),
    INDEX idx_timeseries_metric (metric_name)
);
```

### 1.4 Processing & Queue Tables

#### `processing_queue` (Celery Task Queue State)
```sql
CREATE TABLE processing_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filing_id UUID NOT NULL,

    -- Task identification
    task_id VARCHAR(100) UNIQUE NOT NULL,
    task_type VARCHAR(50) NOT NULL, -- signal_extraction/analysis/comparison

    -- Priority & routing
    priority INTEGER DEFAULT 5, -- 1 (highest) to 10 (lowest)
    model_tier VARCHAR(10),

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- pending/processing/completed/failed/retry
    worker_id VARCHAR(100),

    -- Timing
    queued_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Error handling
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    error_message TEXT,
    error_traceback TEXT,

    -- Performance
    execution_duration_ms INTEGER,

    CONSTRAINT proc_queue_filing_fk FOREIGN KEY (filing_id) REFERENCES filings(id),
    INDEX idx_proc_queue_status (status),
    INDEX idx_proc_queue_priority (priority, queued_at),
    INDEX idx_proc_queue_task (task_id)
);
```

#### `processing_metrics` (System Performance Tracking)
```sql
CREATE TABLE processing_metrics (
    id BIGSERIAL PRIMARY KEY,

    -- Time window
    window_start TIMESTAMP WITH TIME ZONE NOT NULL,
    window_end TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Throughput
    filings_processed INTEGER DEFAULT 0,
    signals_extracted INTEGER DEFAULT 0,
    analyses_completed INTEGER DEFAULT 0,

    -- Performance
    avg_processing_time_ms INTEGER,
    p50_processing_time_ms INTEGER,
    p95_processing_time_ms INTEGER,
    p99_processing_time_ms INTEGER,

    -- Quality
    avg_confidence_score DECIMAL(5,4),
    avg_quality_score DECIMAL(5,4),

    -- Errors
    error_count INTEGER DEFAULT 0,
    retry_count INTEGER DEFAULT 0,

    -- Resource utilization
    cpu_utilization_avg DECIMAL(5,4),
    memory_utilization_avg DECIMAL(5,4),

    -- Model breakdown
    tier1_count INTEGER DEFAULT 0,
    tier2a_count INTEGER DEFAULT 0,
    tier2b_count INTEGER DEFAULT 0,
    tier2c_count INTEGER DEFAULT 0,
    tier2d_count INTEGER DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    INDEX idx_proc_metrics_window (window_start, window_end)
);
```

---

## 2. DUCKDB (LOCAL ANALYTICS) - ANALYTICAL QUERIES

### 2.1 Optimized for Fast Aggregations

```sql
-- Filings table (same structure as Supabase but with DuckDB optimizations)
CREATE TABLE filings (
    id INTEGER PRIMARY KEY,
    cik VARCHAR,
    form_type VARCHAR,
    filing_date DATE,
    accession_number VARCHAR UNIQUE,
    document_url VARCHAR,
    signals JSON,
    analysis JSON,
    signal_count INTEGER,
    model_used VARCHAR,
    created_at TIMESTAMP
);

-- Column-oriented indexes for analytics
CREATE INDEX idx_filing_date ON filings(filing_date);
CREATE INDEX idx_cik ON filings(cik);
CREATE INDEX idx_form_type ON filings(form_type);

-- Signals table for fast filtering
CREATE TABLE signals (
    id INTEGER PRIMARY KEY,
    filing_id INTEGER,
    signal_name VARCHAR,
    signal_category VARCHAR,
    signal_value VARCHAR,
    confidence FLOAT,
    metadata JSON
);

CREATE INDEX idx_signal_filing ON signals(filing_id);
CREATE INDEX idx_signal_name ON signals(signal_name);
CREATE INDEX idx_signal_category ON signals(signal_category);

-- Materialized aggregations for common queries
CREATE TABLE signal_aggregates AS
SELECT
    cik,
    signal_category,
    COUNT(*) as signal_count,
    AVG(CAST(signal_value AS FLOAT)) as avg_value,
    STDDEV(CAST(signal_value AS FLOAT)) as std_value,
    MIN(filing_date) as first_filing,
    MAX(filing_date) as last_filing
FROM filings f
JOIN signals s ON f.id = s.filing_id
GROUP BY cik, signal_category;

-- Time series view for trend analysis
CREATE VIEW signal_trends AS
SELECT
    f.cik,
    s.signal_name,
    f.filing_date,
    CAST(s.signal_value AS FLOAT) as value,
    s.confidence,
    AVG(CAST(s.signal_value AS FLOAT)) OVER (
        PARTITION BY f.cik, s.signal_name
        ORDER BY f.filing_date
        ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
    ) as moving_avg_4q
FROM filings f
JOIN signals s ON f.id = s.filing_id;
```

### 2.2 Parquet Export for Long-Term Storage

```sql
-- Export historical data to Parquet for cold storage
COPY (
    SELECT * FROM filings WHERE filing_date < CURRENT_DATE - INTERVAL 2 YEARS
) TO 'data/historical/filings_2020_2023.parquet' (FORMAT PARQUET, COMPRESSION ZSTD);

-- Export signals
COPY (
    SELECT s.* FROM signals s
    JOIN filings f ON s.filing_id = f.id
    WHERE f.filing_date < CURRENT_DATE - INTERVAL 2 YEARS
) TO 'data/historical/signals_2020_2023.parquet' (FORMAT PARQUET, COMPRESSION ZSTD);
```

---

## 3. REDIS - CACHING LAYER (Sub-100ms Queries)

### 3.1 Cache Key Patterns

```python
# Hot filing cache (most recent filings)
CACHE_KEYS = {
    # Filing data
    "filing:{accession_number}": "JSON",  # Complete filing record
    "filing:signals:{accession_number}": "JSON",  # All signals for filing
    "filing:analysis:{accession_number}": "JSON",  # Analysis results

    # Company data
    "company:{cik}:info": "JSON",  # Company metadata
    "company:{cik}:recent_filings": "LIST",  # Recent filing IDs (FIFO)
    "company:{cik}:signal_summary": "JSON",  # Aggregated signal summary

    # Signal queries
    "signal:definition:{signal_code}": "JSON",  # Signal taxonomy
    "signal:values:{signal_code}:{date_range}": "SORTED_SET",  # Signal values by date

    # Search results
    "search:{query_hash}": "JSON",  # Cached search results

    # Processing status
    "task:{task_id}:status": "JSON",  # Task status
    "queue:pending": "LIST",  # Pending task IDs
    "queue:processing": "SET",  # Currently processing tasks

    # Performance metrics
    "metrics:throughput:{window}": "JSON",  # Throughput statistics
    "metrics:latency:{model}": "JSON",  # Model latency metrics
}
```

### 3.2 Cache Expiration Strategy

```python
CACHE_TTL = {
    # Hot data (frequently accessed)
    "filing:*": 3600,  # 1 hour
    "company:*:recent_filings": 1800,  # 30 minutes
    "signal:definition:*": 86400,  # 24 hours (rarely changes)

    # Warm data
    "company:*:signal_summary": 7200,  # 2 hours
    "search:*": 1800,  # 30 minutes

    # Processing status (ephemeral)
    "task:*:status": 300,  # 5 minutes
    "queue:*": 60,  # 1 minute

    # Metrics (aggregated periodically)
    "metrics:*": 600,  # 10 minutes
}
```

### 3.3 Cache Invalidation Rules

```python
# Invalidate on events
INVALIDATION_RULES = {
    "filing.created": [
        "filing:{accession_number}",
        "company:{cik}:recent_filings",
        "company:{cik}:signal_summary",
    ],
    "signals.extracted": [
        "filing:signals:{accession_number}",
        "signal:values:{signal_code}:*",
    ],
    "analysis.completed": [
        "filing:analysis:{accession_number}",
        "company:{cik}:signal_summary",
    ],
}
```

---

## 4. DATA FLOW & SYNCHRONIZATION

### 4.1 Primary Data Flow

```
SEC EDGAR → Ingestion Queue → Celery Workers
    ↓
    ├─→ Supabase (persistent storage)
    ├─→ DuckDB (analytics sync)
    └─→ Redis (hot cache)
```

### 4.2 Sync Strategy

```python
# Real-time sync: Supabase → Redis
# Triggered on INSERT/UPDATE via Supabase webhooks
def sync_to_redis(table: str, record: dict):
    if table == "filings":
        redis.setex(
            f"filing:{record['accession_number']}",
            3600,
            json.dumps(record)
        )
    # Additional sync logic...

# Batch sync: Supabase → DuckDB (nightly)
# Full sync of recent data for analytics
def nightly_sync_to_duckdb():
    # Sync last 30 days of filings
    query = "SELECT * FROM filings WHERE filing_date >= CURRENT_DATE - 30"
    df = supabase.query(query).to_dataframe()
    duckdb.execute("INSERT OR REPLACE INTO filings SELECT * FROM df")
```

---

## 5. SCHEMA VERSIONING & MIGRATION

```sql
-- Schema version tracking
CREATE TABLE schema_versions (
    version INTEGER PRIMARY KEY,
    description TEXT NOT NULL,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    migration_script TEXT
);

-- Initial version
INSERT INTO schema_versions (version, description) VALUES
    (1, 'Initial schema - filings, companies, signals, analyses');
```

---

## Performance Characteristics

| Layer | Query Type | Target Latency | Use Case |
|-------|-----------|---------------|----------|
| Redis | Key-value lookup | <1ms | Hot filing retrieval |
| Supabase | Indexed query | <50ms | Filing search, signal filtering |
| Supabase | Complex join | <200ms | Network analysis, entity relationships |
| DuckDB | Aggregation | <100ms | Signal trends, company summaries |
| DuckDB | Analytics query | <500ms | Cross-company analysis, correlations |

---

**Document Version**: 1.0
**Last Updated**: 2025-10-18
**Owner**: Data Infrastructure Architect
**Dependencies**: Supabase v2+, DuckDB 0.9+, Redis 7+
