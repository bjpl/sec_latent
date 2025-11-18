"""
Database Optimization Configuration
Optimizes PostgreSQL (Supabase), DuckDB, and connection pooling for maximum performance
"""

from typing import Dict, Any, List
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)


# ============================================
# SUPABASE (PostgreSQL) OPTIMIZATION
# ============================================

SUPABASE_CONNECTION_POOL_CONFIG = {
    # Connection pooling via PgBouncer (Supabase built-in)
    "pool_size": 20,  # Maximum connections per worker
    "max_overflow": 10,  # Additional connections during peak
    "pool_timeout": 30,  # Seconds to wait for connection
    "pool_recycle": 3600,  # Recycle connections every hour
    "pool_pre_ping": True,  # Verify connection before using

    # Statement timeout
    "connect_args": {
        "options": "-c statement_timeout=30000",  # 30 second query timeout
        "connect_timeout": 5,  # 5 second connection timeout
        "application_name": "sec_filing_analyzer",
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 3,
    }
}


# Optimized indexes for SEC filing data
SUPABASE_INDEX_DEFINITIONS = [
    {
        "name": "idx_filings_cik_filing_date",
        "table": "filings",
        "columns": ["cik", "filing_date DESC"],
        "type": "btree",
        "purpose": "Fast company filing lookup by date"
    },
    {
        "name": "idx_filings_form_type_filing_date",
        "table": "filings",
        "columns": ["form_type", "filing_date DESC"],
        "type": "btree",
        "purpose": "Fast form type searches"
    },
    {
        "name": "idx_filings_accession_number",
        "table": "filings",
        "columns": ["accession_number"],
        "type": "btree",
        "unique": True,
        "purpose": "Unique filing lookups"
    },
    {
        "name": "idx_filings_created_at",
        "table": "filings",
        "columns": ["created_at DESC"],
        "type": "brin",  # Block Range Index for time-series
        "purpose": "Efficient time-based queries"
    },
    {
        "name": "idx_filings_signals_gin",
        "table": "filings",
        "columns": ["signals"],
        "type": "gin",  # Generalized Inverted Index for JSON
        "purpose": "Fast JSON signal searches"
    },
    {
        "name": "idx_signals_filing_id_category",
        "table": "signals",
        "columns": ["filing_id", "signal_category"],
        "type": "btree",
        "purpose": "Fast signal category filtering"
    },
    {
        "name": "idx_signals_name_confidence",
        "table": "signals",
        "columns": ["signal_name", "confidence DESC"],
        "type": "btree",
        "purpose": "High-confidence signal queries"
    },
    {
        "name": "idx_audit_logs_user_timestamp",
        "table": "audit_logs",
        "columns": ["user_id", "timestamp DESC"],
        "type": "btree",
        "purpose": "User activity audit trails"
    },
    {
        "name": "idx_audit_logs_action_timestamp",
        "table": "audit_logs",
        "columns": ["action", "timestamp DESC"],
        "type": "btree",
        "purpose": "Action-based audit queries"
    },
    {
        "name": "idx_audit_logs_timestamp_brin",
        "table": "audit_logs",
        "columns": ["timestamp"],
        "type": "brin",
        "purpose": "Time-series audit log queries"
    }
]


# Table partitioning strategy for 7-year retention
SUPABASE_PARTITION_CONFIG = {
    "audit_logs": {
        "partition_by": "RANGE (timestamp)",
        "partition_interval": "1 MONTH",
        "retention_period": "7 YEARS",
        "partition_template": """
            CREATE TABLE IF NOT EXISTS audit_logs_y{year}m{month}
            PARTITION OF audit_logs
            FOR VALUES FROM ('{start_date}') TO ('{end_date}');
        """,
        "auto_create_partitions": True,
        "partition_maintenance_schedule": "0 0 * * 0"  # Weekly on Sunday
    },
    "filings": {
        "partition_by": "RANGE (filing_date)",
        "partition_interval": "1 YEAR",
        "retention_period": "INDEFINITE",  # SEC filings retained forever
        "partition_template": """
            CREATE TABLE IF NOT EXISTS filings_y{year}
            PARTITION OF filings
            FOR VALUES FROM ('{start_date}') TO ('{end_date}');
        """
    }
}


# Query optimization settings
SUPABASE_QUERY_OPTIMIZATION = {
    # Materialized views for common aggregations
    "materialized_views": [
        {
            "name": "mv_company_signal_summary",
            "query": """
                CREATE MATERIALIZED VIEW mv_company_signal_summary AS
                SELECT
                    f.cik,
                    f.form_type,
                    COUNT(*) as filing_count,
                    SUM(f.signal_count) as total_signals,
                    AVG(f.signal_count) as avg_signals_per_filing,
                    MAX(f.filing_date) as latest_filing_date
                FROM filings f
                GROUP BY f.cik, f.form_type
                WITH DATA;

                CREATE UNIQUE INDEX ON mv_company_signal_summary (cik, form_type);
            """,
            "refresh_schedule": "0 1 * * *",  # Daily at 1 AM
            "refresh_concurrently": True
        },
        {
            "name": "mv_signal_trends",
            "query": """
                CREATE MATERIALIZED VIEW mv_signal_trends AS
                SELECT
                    s.signal_name,
                    s.signal_category,
                    DATE_TRUNC('month', f.filing_date) as month,
                    COUNT(*) as occurrence_count,
                    AVG(s.confidence) as avg_confidence
                FROM signals s
                JOIN filings f ON s.filing_id = f.id
                WHERE f.filing_date >= NOW() - INTERVAL '2 years'
                GROUP BY s.signal_name, s.signal_category, DATE_TRUNC('month', f.filing_date)
                WITH DATA;

                CREATE INDEX ON mv_signal_trends (signal_name, month DESC);
            """,
            "refresh_schedule": "0 2 * * *",  # Daily at 2 AM
            "refresh_concurrently": True
        }
    ],

    # Connection pooler settings (PgBouncer via Supabase)
    "pgbouncer_config": {
        "pool_mode": "transaction",  # Transaction pooling for best performance
        "default_pool_size": 25,
        "max_client_conn": 1000,
        "reserve_pool_size": 5,
        "reserve_pool_timeout": 3,
        "max_db_connections": 100,
        "max_user_connections": 100
    },

    # Query performance settings
    "performance_settings": {
        "work_mem": "256MB",  # Memory per query operation
        "shared_buffers": "4GB",  # Shared memory buffer
        "effective_cache_size": "12GB",  # OS cache estimation
        "maintenance_work_mem": "1GB",  # Memory for maintenance ops
        "random_page_cost": 1.1,  # SSD optimization (default 4.0)
        "effective_io_concurrency": 200,  # SSD parallel I/O
        "max_parallel_workers_per_gather": 4,
        "max_parallel_workers": 8,
        "max_worker_processes": 8,
        "default_statistics_target": 500,  # Better query planning
    }
}


# ============================================
# DUCKDB OPTIMIZATION
# ============================================

DUCKDB_CONFIG = {
    "memory_limit": "8GB",  # Maximum memory for DuckDB
    "threads": 8,  # Parallel query execution
    "max_memory": "8GB",
    "temp_directory": "/tmp/duckdb",

    # Performance settings
    "enable_object_cache": True,
    "enable_http_metadata_cache": True,
    "force_compression": "auto",
    "preserve_insertion_order": False,  # Faster for analytical queries

    # Query optimization
    "enable_profiling": False,  # Disable in production for performance
    "enable_progress_bar": False,
    "experimental_parallel_csv": True,

    # Storage optimization
    "checkpoint_threshold": "256MB",
    "wal_autocheckpoint": 1000,
}


DUCKDB_INDEX_DEFINITIONS = [
    {
        "name": "idx_filings_cik",
        "table": "filings",
        "columns": ["cik"],
        "type": "btree"
    },
    {
        "name": "idx_filings_filing_date",
        "table": "filings",
        "columns": ["filing_date"],
        "type": "btree"
    },
    {
        "name": "idx_signals_filing_id",
        "table": "signals",
        "columns": ["filing_id"],
        "type": "btree"
    },
    {
        "name": "idx_signals_category_name",
        "table": "signals",
        "columns": ["signal_category", "signal_name"],
        "type": "btree"
    }
]


# ============================================
# DATABASE MAINTENANCE
# ============================================

DATABASE_MAINTENANCE_SCHEDULE = {
    "vacuum_analyze": {
        "schedule": "0 3 * * 0",  # Weekly on Sunday at 3 AM
        "tables": ["filings", "signals", "audit_logs"],
        "full": False,  # VACUUM without FULL (less disruptive)
        "analyze": True
    },
    "reindex": {
        "schedule": "0 4 * * 0",  # Weekly on Sunday at 4 AM
        "tables": ["filings", "signals"],
        "concurrently": True
    },
    "partition_maintenance": {
        "schedule": "0 5 * * 0",  # Weekly on Sunday at 5 AM
        "create_future_partitions": 2,  # Create 2 months ahead
        "drop_old_partitions": True,
        "retention_check": True
    },
    "statistics_update": {
        "schedule": "0 2 * * *",  # Daily at 2 AM
        "auto_analyze": True
    }
}


# ============================================
# MONITORING QUERIES
# ============================================

DATABASE_MONITORING_QUERIES = {
    "connection_count": """
        SELECT count(*) as connections
        FROM pg_stat_activity
        WHERE datname = current_database();
    """,

    "active_queries": """
        SELECT
            pid,
            usename,
            application_name,
            state,
            query,
            wait_event_type,
            wait_event,
            query_start,
            state_change,
            EXTRACT(EPOCH FROM (NOW() - query_start)) as duration_seconds
        FROM pg_stat_activity
        WHERE state != 'idle'
        AND query NOT LIKE '%pg_stat_activity%'
        ORDER BY query_start;
    """,

    "slow_queries": """
        SELECT
            query,
            calls,
            total_exec_time,
            mean_exec_time,
            stddev_exec_time,
            rows
        FROM pg_stat_statements
        WHERE mean_exec_time > 100  -- Queries slower than 100ms
        ORDER BY mean_exec_time DESC
        LIMIT 20;
    """,

    "table_sizes": """
        SELECT
            schemaname,
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
            pg_total_relation_size(schemaname||'.'||tablename) AS size_bytes
        FROM pg_tables
        WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
        ORDER BY size_bytes DESC;
    """,

    "index_usage": """
        SELECT
            schemaname,
            tablename,
            indexname,
            idx_scan as index_scans,
            idx_tup_read as tuples_read,
            idx_tup_fetch as tuples_fetched,
            pg_size_pretty(pg_relation_size(indexrelid)) as index_size
        FROM pg_stat_user_indexes
        ORDER BY idx_scan ASC, pg_relation_size(indexrelid) DESC;
    """,

    "cache_hit_ratio": """
        SELECT
            'cache_hit_ratio' as metric,
            sum(heap_blks_hit) / nullif(sum(heap_blks_hit) + sum(heap_blks_read), 0) as ratio
        FROM pg_statio_user_tables;
    """,

    "replication_lag": """
        SELECT
            client_addr,
            state,
            sent_lsn,
            write_lsn,
            flush_lsn,
            replay_lsn,
            sync_state,
            pg_wal_lsn_diff(sent_lsn, replay_lsn) as lag_bytes
        FROM pg_stat_replication;
    """
}


# ============================================
# OPTIMIZATION FUNCTIONS
# ============================================

def generate_create_index_sql(index_config: Dict[str, Any]) -> str:
    """Generate CREATE INDEX SQL from configuration"""
    unique = "UNIQUE " if index_config.get("unique", False) else ""
    concurrently = "CONCURRENTLY " if index_config.get("concurrently", True) else ""
    index_type = index_config.get("type", "btree").upper()

    columns = ", ".join(index_config["columns"]) if isinstance(index_config["columns"], list) else index_config["columns"]

    sql = f"""
        CREATE {unique}INDEX {concurrently}IF NOT EXISTS {index_config['name']}
        ON {index_config['table']} USING {index_type}
        ({columns});
    """

    if "purpose" in index_config:
        sql += f"\n-- Purpose: {index_config['purpose']}"

    return sql.strip()


def generate_partition_sql(table: str, config: Dict[str, Any], year: int, month: int = None) -> str:
    """Generate partition creation SQL"""
    if config["partition_interval"] == "1 MONTH":
        from datetime import datetime
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)

        return config["partition_template"].format(
            year=year,
            month=f"{month:02d}",
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d")
        )

    elif config["partition_interval"] == "1 YEAR":
        from datetime import datetime
        start_date = datetime(year, 1, 1)
        end_date = datetime(year + 1, 1, 1)

        return config["partition_template"].format(
            year=year,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d")
        )


def get_optimization_summary() -> Dict[str, Any]:
    """Get summary of database optimizations"""
    return {
        "connection_pool": {
            "pool_size": SUPABASE_CONNECTION_POOL_CONFIG["pool_size"],
            "max_overflow": SUPABASE_CONNECTION_POOL_CONFIG["max_overflow"],
            "pool_timeout": SUPABASE_CONNECTION_POOL_CONFIG["pool_timeout"]
        },
        "indexes": {
            "supabase_count": len(SUPABASE_INDEX_DEFINITIONS),
            "duckdb_count": len(DUCKDB_INDEX_DEFINITIONS)
        },
        "partitioning": {
            "enabled_tables": list(SUPABASE_PARTITION_CONFIG.keys()),
            "retention_periods": {
                table: config["retention_period"]
                for table, config in SUPABASE_PARTITION_CONFIG.items()
            }
        },
        "maintenance": {
            "schedules": list(DATABASE_MAINTENANCE_SCHEDULE.keys())
        },
        "monitoring": {
            "queries_count": len(DATABASE_MONITORING_QUERIES)
        }
    }


if __name__ == "__main__":
    # Generate all index creation SQL
    print("=== SUPABASE INDEX CREATION SQL ===\n")
    for index_config in SUPABASE_INDEX_DEFINITIONS:
        print(generate_create_index_sql(index_config))
        print()

    print("\n=== OPTIMIZATION SUMMARY ===\n")
    import json
    print(json.dumps(get_optimization_summary(), indent=2))
