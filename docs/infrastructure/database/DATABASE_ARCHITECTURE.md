# PostgreSQL Database Architecture

## Overview

The SEC Latent platform uses PostgreSQL 15 as the primary relational database with high-availability configuration, optimized for analytical workloads and regulatory compliance.

## Database Design Principles

1. **Normalization**: 3NF for transactional data
2. **Denormalization**: Strategic for analytics queries
3. **Partitioning**: Time-based for audit logs (7-year retention)
4. **Indexing**: Covering indexes for frequent queries
5. **Constraints**: Enforce data integrity at database level

## Database Schema

### Core Tables

```sql
-- Companies Table
CREATE TABLE companies (
    company_id SERIAL PRIMARY KEY,
    cik VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    sic_code VARCHAR(4),
    industry VARCHAR(100),
    state_of_incorporation VARCHAR(2),
    fiscal_year_end INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT check_cik_format CHECK (cik ~ '^\d{10}$')
);

CREATE INDEX idx_companies_cik ON companies(cik);
CREATE INDEX idx_companies_industry ON companies(industry);
CREATE INDEX idx_companies_sic ON companies(sic_code);

-- Filings Table
CREATE TABLE filings (
    filing_id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(company_id),
    accession_number VARCHAR(20) UNIQUE NOT NULL,
    filing_type VARCHAR(20) NOT NULL,
    filing_date DATE NOT NULL,
    report_period DATE,
    document_url TEXT,
    filing_html TEXT,
    filing_text TEXT,
    file_size_bytes BIGINT,
    processing_status VARCHAR(20) DEFAULT 'pending',
    processed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT check_accession_format CHECK (accession_number ~ '^\d{10}-\d{2}-\d{6}$')
);

CREATE INDEX idx_filings_company ON filings(company_id);
CREATE INDEX idx_filings_date ON filings(filing_date DESC);
CREATE INDEX idx_filings_type ON filings(filing_type);
CREATE INDEX idx_filings_status ON filings(processing_status);
CREATE INDEX idx_filings_accession ON filings(accession_number);

-- Signals Table (150 signals per filing)
CREATE TABLE signals (
    signal_id BIGSERIAL PRIMARY KEY,
    filing_id INTEGER NOT NULL REFERENCES filings(filing_id) ON DELETE CASCADE,
    signal_category VARCHAR(50) NOT NULL, -- 'financial', 'sentiment', 'risk', 'management'
    signal_name VARCHAR(100) NOT NULL,
    signal_value NUMERIC(15, 6),
    signal_text TEXT,
    confidence_score NUMERIC(3, 2),
    extracted_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT check_confidence CHECK (confidence_score BETWEEN 0 AND 1),
    CONSTRAINT check_category CHECK (signal_category IN ('financial', 'sentiment', 'risk', 'management'))
);

CREATE INDEX idx_signals_filing ON signals(filing_id);
CREATE INDEX idx_signals_category ON signals(signal_category);
CREATE INDEX idx_signals_name ON signals(signal_name);
CREATE INDEX idx_signals_extracted ON signals(extracted_at DESC);

-- Composite index for common query patterns
CREATE INDEX idx_signals_filing_category ON signals(filing_id, signal_category);

-- Analysis Results Table
CREATE TABLE analysis_results (
    analysis_id BIGSERIAL PRIMARY KEY,
    filing_id INTEGER NOT NULL REFERENCES filings(filing_id) ON DELETE CASCADE,
    model_used VARCHAR(50) NOT NULL, -- 'sonnet', 'haiku', 'opus'
    analysis_type VARCHAR(50) NOT NULL,
    result_json JSONB NOT NULL,
    token_count INTEGER,
    processing_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_analysis_filing ON analysis_results(filing_id);
CREATE INDEX idx_analysis_model ON analysis_results(model_used);
CREATE INDEX idx_analysis_type ON analysis_results(analysis_type);
CREATE INDEX idx_analysis_created ON analysis_results(created_at DESC);

-- JSONB GIN index for fast JSON queries
CREATE INDEX idx_analysis_result_gin ON analysis_results USING GIN (result_json);

-- Audit Logs Table (Partitioned by Month)
CREATE TABLE audit_logs (
    log_id BIGSERIAL,
    user_id VARCHAR(100),
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    ip_address INET,
    user_agent TEXT,
    request_method VARCHAR(10),
    request_path TEXT,
    status_code INTEGER,
    response_time_ms INTEGER,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (log_id, created_at)
) PARTITION BY RANGE (created_at);

-- Create partitions for 7 years (84 months)
-- Script to generate partitions:
-- DO $$
-- DECLARE
--     start_date DATE := '2025-01-01';
--     end_date DATE := '2032-01-01';
--     partition_date DATE;
-- BEGIN
--     partition_date := start_date;
--     WHILE partition_date < end_date LOOP
--         EXECUTE format(
--             'CREATE TABLE IF NOT EXISTS audit_logs_%s PARTITION OF audit_logs
--              FOR VALUES FROM (%L) TO (%L)',
--             to_char(partition_date, 'YYYY_MM'),
--             partition_date,
--             partition_date + INTERVAL '1 month'
--         );
--         partition_date := partition_date + INTERVAL '1 month';
--     END LOOP;
-- END $$;

CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_action ON audit_logs(action);
CREATE INDEX idx_audit_created ON audit_logs(created_at DESC);
CREATE INDEX idx_audit_metadata_gin ON audit_logs USING GIN (metadata);

-- Users Table (OAuth integration)
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    oauth_provider VARCHAR(50),
    oauth_id VARCHAR(255),
    role VARCHAR(50) DEFAULT 'viewer',
    is_active BOOLEAN DEFAULT true,
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT check_role CHECK (role IN ('viewer', 'analyst', 'admin', 'superadmin'))
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_oauth ON users(oauth_provider, oauth_id);
CREATE INDEX idx_users_role ON users(role);

-- API Keys Table
CREATE TABLE api_keys (
    key_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    key_hash VARCHAR(64) NOT NULL UNIQUE,
    key_prefix VARCHAR(8) NOT NULL,
    name VARCHAR(100),
    scopes VARCHAR(255)[] DEFAULT '{}',
    rate_limit INTEGER DEFAULT 100,
    expires_at TIMESTAMP,
    last_used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_user ON api_keys(user_id);
CREATE INDEX idx_api_keys_active ON api_keys(is_active, expires_at);
```

## Replication Strategy

### Primary-Replica Configuration

```
┌─────────────┐
│   Primary   │ ─────┐
│  (Read/Write)│      │
└─────────────┘      │ Async Replication
                     │
        ┌────────────┴────────────┐
        │                         │
┌───────▼───────┐         ┌───────▼───────┐
│   Replica 1   │         │   Replica 2   │
│  (Read Only)  │         │  (Read Only)  │
└───────────────┘         └───────────────┘
```

### Configuration

**postgresql.conf** (Primary):
```ini
# Replication Settings
wal_level = replica
max_wal_senders = 10
max_replication_slots = 10
wal_keep_size = 1GB

# Performance Tuning
shared_buffers = 4GB
effective_cache_size = 12GB
maintenance_work_mem = 1GB
work_mem = 64MB
max_connections = 200

# Query Optimization
random_page_cost = 1.1
effective_io_concurrency = 200
max_parallel_workers_per_gather = 4
max_parallel_workers = 8

# Logging
log_min_duration_statement = 1000
log_line_prefix = '%m [%p] %u@%d '
log_checkpoints = on
log_connections = on
log_disconnections = on

# Autovacuum
autovacuum = on
autovacuum_max_workers = 4
autovacuum_naptime = 30s
```

**pg_hba.conf** (Access Control):
```
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             postgres                                peer
host    all             all             10.0.0.0/8              scram-sha-256
host    replication     replicator      10.0.1.0/24             scram-sha-256
hostssl all             all             0.0.0.0/0               scram-sha-256
```

## Connection Pooling

### PgBouncer Configuration

**pgbouncer.ini**:
```ini
[databases]
sec_latent = host=postgres port=5432 dbname=sec_latent

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
auth_type = scram-sha-256
auth_file = /etc/pgbouncer/userlist.txt

# Pool settings
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
reserve_pool_size = 5
reserve_pool_timeout = 3

# Connection limits
server_lifetime = 3600
server_idle_timeout = 600
server_connect_timeout = 15

# Logging
log_connections = 1
log_disconnections = 1
log_pooler_errors = 1
```

**Application Connection String**:
```
postgresql://user:pass@pgbouncer:6432/sec_latent?pool_size=25&max_overflow=5
```

## Backup Strategy

### Automated Backups

```bash
#!/bin/bash
# /scripts/postgres-backup.sh

# Configuration
BACKUP_DIR="/backups/postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30
DATABASE="sec_latent"

# Full backup
pg_dump -Fc -h postgres -U secuser -d $DATABASE > \
    $BACKUP_DIR/full_${TIMESTAMP}.dump

# Upload to S3
aws s3 cp $BACKUP_DIR/full_${TIMESTAMP}.dump \
    s3://sec-latent-backups/postgres/full_${TIMESTAMP}.dump

# Delete old backups
find $BACKUP_DIR -name "full_*.dump" -mtime +$RETENTION_DAYS -delete

# Incremental WAL archiving
rsync -av /var/lib/postgresql/15/main/pg_wal/ \
    s3://sec-latent-backups/postgres/wal/

echo "Backup completed: full_${TIMESTAMP}.dump"
```

**Cron Schedule**:
```cron
# Full backup daily at 2 AM
0 2 * * * /scripts/postgres-backup.sh

# WAL archiving every 15 minutes
*/15 * * * * /scripts/postgres-wal-archive.sh
```

### Point-in-Time Recovery (PITR)

```bash
#!/bin/bash
# Restore to specific point in time

TARGET_TIME="2025-10-19 03:00:00"
BACKUP_FILE="full_20251019_020000.dump"

# Stop PostgreSQL
systemctl stop postgresql

# Restore base backup
pg_restore -Fc -h localhost -U postgres -d sec_latent $BACKUP_FILE

# Configure recovery
cat > /var/lib/postgresql/15/main/recovery.conf <<EOF
restore_command = 'cp /backups/postgres/wal/%f %p'
recovery_target_time = '$TARGET_TIME'
recovery_target_action = promote
EOF

# Start PostgreSQL
systemctl start postgresql
```

## Performance Optimization

### Indexing Strategy

```sql
-- Analyze query patterns
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY relname;

-- Create covering indexes for common queries
CREATE INDEX idx_filings_company_date_status
ON filings(company_id, filing_date DESC, processing_status)
INCLUDE (filing_type, accession_number);

-- Partial indexes for filtered queries
CREATE INDEX idx_filings_pending
ON filings(filing_date DESC)
WHERE processing_status = 'pending';

-- GIN indexes for full-text search
CREATE INDEX idx_filings_text_search
ON filings USING GIN(to_tsvector('english', filing_text));
```

### Query Optimization

```sql
-- Enable pg_stat_statements
CREATE EXTENSION pg_stat_statements;

-- Identify slow queries
SELECT
    query,
    calls,
    total_exec_time,
    mean_exec_time,
    stddev_exec_time
FROM pg_stat_statements
WHERE mean_exec_time > 100
ORDER BY mean_exec_time DESC
LIMIT 20;

-- Optimize specific query
EXPLAIN (ANALYZE, BUFFERS)
SELECT f.*, c.name
FROM filings f
JOIN companies c ON f.company_id = c.company_id
WHERE f.filing_date >= '2024-01-01'
  AND f.processing_status = 'completed'
ORDER BY f.filing_date DESC
LIMIT 100;
```

### Partitioning

```sql
-- List partitions
SELECT
    parent.relname AS parent_table,
    child.relname AS partition_name,
    pg_get_expr(child.relpartbound, child.oid) AS partition_bounds
FROM pg_inherits
JOIN pg_class parent ON pg_inherits.inhparent = parent.oid
JOIN pg_class child ON pg_inherits.inhrelid = child.oid
WHERE parent.relname = 'audit_logs'
ORDER BY child.relname;

-- Drop old partitions (after 7 years)
DROP TABLE audit_logs_2018_01;
```

## Monitoring

### Key Metrics

```sql
-- Database size
SELECT
    pg_database.datname,
    pg_size_pretty(pg_database_size(pg_database.datname)) AS size
FROM pg_database
ORDER BY pg_database_size(pg_database.datname) DESC;

-- Table sizes
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    pg_total_relation_size(schemaname||'.'||tablename) AS bytes
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY bytes DESC;

-- Connection count
SELECT
    state,
    COUNT(*)
FROM pg_stat_activity
WHERE datname = 'sec_latent'
GROUP BY state;

-- Cache hit rate (should be >99%)
SELECT
    sum(heap_blks_read) as heap_read,
    sum(heap_blks_hit) as heap_hit,
    sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) as cache_hit_ratio
FROM pg_statio_user_tables;

-- Index usage
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;
```

### Prometheus Exporter

**docker-compose.yml** addition:
```yaml
postgres-exporter:
  image: prometheuscommunity/postgres-exporter:latest
  environment:
    DATA_SOURCE_NAME: "postgresql://exporter:${EXPORTER_PASSWORD}@postgres:5432/sec_latent?sslmode=disable"
  ports:
    - "9187:9187"
  networks:
    - sec-latent-network
```

**Custom Queries** (queries.yaml):
```yaml
pg_database_size:
  query: "SELECT pg_database.datname, pg_database_size(pg_database.datname) as bytes FROM pg_database"
  metrics:
    - datname:
        usage: "LABEL"
        description: "Database name"
    - bytes:
        usage: "GAUGE"
        description: "Database size in bytes"

pg_table_sizes:
  query: "SELECT tablename, pg_total_relation_size(schemaname||'.'||tablename) as bytes FROM pg_tables WHERE schemaname = 'public'"
  metrics:
    - tablename:
        usage: "LABEL"
        description: "Table name"
    - bytes:
        usage: "GAUGE"
        description: "Table size in bytes"
```

## Security

### Encryption

```sql
-- Enable pgcrypto extension
CREATE EXTENSION pgcrypto;

-- Encrypt sensitive data
CREATE TABLE encrypted_data (
    id SERIAL PRIMARY KEY,
    sensitive_data BYTEA NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Insert encrypted data
INSERT INTO encrypted_data (sensitive_data)
VALUES (pgp_sym_encrypt('secret data', 'encryption_key'));

-- Query encrypted data
SELECT pgp_sym_decrypt(sensitive_data, 'encryption_key')
FROM encrypted_data;
```

### Row-Level Security

```sql
-- Enable RLS
ALTER TABLE filings ENABLE ROW LEVEL SECURITY;

-- Policy for viewers
CREATE POLICY viewer_policy ON filings
    FOR SELECT
    TO viewer_role
    USING (processing_status = 'completed');

-- Policy for analysts
CREATE POLICY analyst_policy ON filings
    FOR ALL
    TO analyst_role
    USING (true);
```

### Audit Trail

```sql
-- Create audit trigger function
CREATE OR REPLACE FUNCTION audit_trigger()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_logs (
        user_id,
        action,
        resource_type,
        resource_id,
        metadata
    ) VALUES (
        current_user,
        TG_OP,
        TG_TABLE_NAME,
        NEW.id,
        jsonb_build_object(
            'old', row_to_json(OLD),
            'new', row_to_json(NEW)
        )
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to tables
CREATE TRIGGER audit_filings
AFTER INSERT OR UPDATE OR DELETE ON filings
FOR EACH ROW EXECUTE FUNCTION audit_trigger();
```

## Disaster Recovery

### Recovery Time Objective (RTO): < 1 hour
### Recovery Point Objective (RPO): < 15 minutes

### Failover Procedure

1. **Detect Primary Failure** (automated via health checks)
2. **Promote Replica to Primary** (< 30 seconds)
   ```bash
   pg_ctl promote -D /var/lib/postgresql/15/main
   ```
3. **Update Application Connection Strings** (< 2 minutes)
4. **Verify Write Operations** (< 1 minute)
5. **Rebuild Failed Primary as Replica** (< 30 minutes)

### Automated Failover with Patroni

**patroni.yml**:
```yaml
scope: sec-latent
name: postgres-1

restapi:
  listen: 0.0.0.0:8008
  connect_address: postgres-1:8008

etcd:
  hosts: etcd-1:2379,etcd-2:2379,etcd-3:2379

bootstrap:
  dcs:
    ttl: 30
    loop_wait: 10
    retry_timeout: 10
    maximum_lag_on_failover: 1048576

postgresql:
  listen: 0.0.0.0:5432
  connect_address: postgres-1:5432
  data_dir: /var/lib/postgresql/15/main
  authentication:
    replication:
      username: replicator
      password: ${REPLICATION_PASSWORD}
    superuser:
      username: postgres
      password: ${POSTGRES_PASSWORD}
```

## Maintenance Procedures

### Routine Maintenance (Weekly)

```sql
-- Vacuum and analyze
VACUUM ANALYZE;

-- Reindex
REINDEX DATABASE sec_latent;

-- Update statistics
ANALYZE;
```

### Partition Management (Monthly)

```bash
#!/bin/bash
# Create next month's partition

NEXT_MONTH=$(date -d "+1 month" +%Y_%m)
START_DATE=$(date -d "+1 month" +%Y-%m-01)
END_DATE=$(date -d "+2 months" +%Y-%m-01)

psql -d sec_latent -c "
CREATE TABLE IF NOT EXISTS audit_logs_${NEXT_MONTH}
PARTITION OF audit_logs
FOR VALUES FROM ('${START_DATE}') TO ('${END_DATE}');
"
```

## Capacity Planning

### Current Usage (as of 2025-10-19)
- Database Size: 50 GB
- Daily Growth: 500 MB
- Query Load: 1,000 QPS
- Connection Pool: 50 connections

### 12-Month Projection
- Database Size: 250 GB
- Daily Growth: 2 GB
- Query Load: 5,000 QPS
- Connection Pool: 200 connections

### Scaling Strategy
1. **0-6 months**: Vertical scaling (increase CPU/RAM)
2. **6-12 months**: Add read replicas (3 replicas)
3. **12+ months**: Consider sharding by company or date range
