"""
Redis Cache Optimization Configuration
Optimizes Redis for maximum cache performance with 95%+ hit rate
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import timedelta

logger = logging.getLogger(__name__)


# ============================================
# REDIS CONNECTION CONFIGURATION
# ============================================

REDIS_CONNECTION_CONFIG = {
    # Connection pooling
    "max_connections": 100,  # Maximum connections in pool
    "socket_keepalive": True,
    "socket_keepalive_options": {
        1: 1,  # TCP_KEEPIDLE
        2: 1,  # TCP_KEEPINTVL
        3: 3   # TCP_KEEPCNT
    },
    "socket_connect_timeout": 5,
    "socket_timeout": 5,
    "retry_on_timeout": True,
    "retry_on_error": [ConnectionError, TimeoutError],
    "retry": {
        "retries": 3,
        "backoff_factor": 0.5,
        "backoff_max": 2.0
    },

    # Health check
    "health_check_interval": 30,  # Seconds
    "client_name": "sec_filing_analyzer",

    # Encoding
    "encoding": "utf-8",
    "encoding_errors": "strict",
    "decode_responses": True
}


# ============================================
# REDIS SERVER CONFIGURATION
# ============================================

REDIS_SERVER_CONFIG = {
    # Memory management
    "maxmemory": "4gb",
    "maxmemory_policy": "allkeys-lru",  # Evict least recently used keys
    "maxmemory_samples": 10,  # LRU sample size for better accuracy

    # Persistence (for cache, use RDB for disaster recovery only)
    "save": "900 1 300 10 60 10000",  # RDB snapshots
    "rdbcompression": "yes",
    "rdbchecksum": "yes",
    "stop_writes_on_bgsave_error": "no",  # Don't stop on save errors

    # AOF (Append-Only File) - Disabled for cache
    "appendonly": "no",

    # Performance
    "tcp_backlog": 511,
    "timeout": 300,  # Close idle connections after 5 minutes
    "tcp_keepalive": 300,
    "lazyfree_lazy_eviction": "yes",  # Async eviction
    "lazyfree_lazy_expire": "yes",
    "lazyfree_lazy_server_del": "yes",

    # Threading
    "io_threads": 4,  # I/O threads for network
    "io_threads_do_reads": "yes",

    # Slow log
    "slowlog_log_slower_than": 10000,  # Log queries > 10ms
    "slowlog_max_len": 128,

    # Latency monitoring
    "latency_monitor_threshold": 100,  # Log events > 100ms
}


# ============================================
# CACHE KEY STRATEGIES
# ============================================

CACHE_KEY_PREFIXES = {
    # Filing data
    "FILING_METADATA": "filing:meta",
    "FILING_TEXT": "filing:text",
    "FILING_ANALYSIS": "filing:analysis",
    "FILING_SIGNALS": "filing:signals",

    # Predictions
    "PREDICTION": "prediction",
    "PREDICTION_BATCH": "prediction:batch",

    # Signals
    "SIGNAL": "signal",
    "SIGNAL_SUMMARY": "signal:summary",

    # Validation
    "VALIDATION_RESULT": "validation:result",
    "VALIDATION_METRICS": "validation:metrics",

    # Market data
    "MARKET_DATA": "market:data",
    "MARKET_SNAPSHOT": "market:snapshot",

    # Company info
    "COMPANY_INFO": "company:info",
    "COMPANY_FILINGS_LIST": "company:filings",

    # User sessions
    "USER_SESSION": "session",
    "USER_PREFERENCES": "user:prefs",

    # API rate limiting
    "RATE_LIMIT": "ratelimit",

    # Temporary data
    "TEMP": "temp",
}


# ============================================
# TTL CONFIGURATION (Graduated Strategy)
# ============================================

CACHE_TTL_STRATEGY = {
    # Frequently accessed data - Long TTL
    "FILING_METADATA": {
        "default": 7200,  # 2 hours
        "high_traffic": 14400,  # 4 hours for popular companies
        "historical": 86400  # 24 hours for old filings (unlikely to change)
    },

    # Computed results - Medium TTL
    "FILING_ANALYSIS": {
        "default": 3600,  # 1 hour
        "recent": 1800,  # 30 minutes for recent filings (may be updated)
        "final": 43200  # 12 hours for finalized analysis
    },

    # Real-time data - Short TTL
    "MARKET_DATA": {
        "default": 300,  # 5 minutes
        "snapshot": 60,  # 1 minute for market snapshots
        "historical": 3600  # 1 hour for historical data
    },

    # Expensive computations - Very long TTL
    "SIGNAL_SUMMARY": {
        "default": 86400,  # 24 hours
        "company_aggregate": 604800  # 7 days for company aggregates
    },

    # User data - Short TTL
    "USER_SESSION": {
        "default": 1800,  # 30 minutes
        "remember_me": 2592000  # 30 days if "remember me"
    },

    # Rate limiting - Very short TTL
    "RATE_LIMIT": {
        "default": 60,  # 1 minute window
        "burst": 1  # 1 second for burst protection
    },

    # Temporary data - Very short TTL
    "TEMP": {
        "default": 300,  # 5 minutes
        "processing": 600  # 10 minutes for in-progress operations
    }
}


# ============================================
# CACHE WARMING STRATEGIES
# ============================================

CACHE_WARMING_CONFIG = {
    "enabled": True,
    "strategies": [
        {
            "name": "popular_companies",
            "description": "Pre-cache filings for most-accessed companies",
            "schedule": "0 */6 * * *",  # Every 6 hours
            "companies": [
                "0000789019",  # Microsoft
                "0000320193",  # Apple
                "0001652044",  # Alphabet (Google)
                "0001018724",  # Amazon
                "0001326801",  # Meta (Facebook)
                "0001318605",  # Tesla
                "0001045810",  # NVIDIA
            ],
            "form_types": ["10-K", "10-Q", "8-K"],
            "count_per_company": 10,
            "priority": "high"
        },
        {
            "name": "recent_filings",
            "description": "Pre-cache most recent filings across all companies",
            "schedule": "0 */2 * * *",  # Every 2 hours
            "query": "SELECT DISTINCT cik FROM filings WHERE filing_date >= NOW() - INTERVAL '7 days' ORDER BY filing_date DESC LIMIT 100",
            "priority": "medium"
        },
        {
            "name": "predictive_warming",
            "description": "Pre-cache related filings based on access patterns",
            "enabled": True,
            "rules": [
                {
                    "trigger": "access_filing",
                    "action": "cache_related_filings",
                    "related": ["same_company", "same_form_type", "same_quarter"]
                },
                {
                    "trigger": "access_company",
                    "action": "cache_company_summary",
                    "include": ["filing_list", "signal_trends", "predictions"]
                }
            ]
        }
    ]
}


# ============================================
# CACHE INVALIDATION STRATEGIES
# ============================================

CACHE_INVALIDATION_CONFIG = {
    "strategies": [
        {
            "name": "cascade_invalidation",
            "description": "Invalidate dependent caches when parent changes",
            "rules": [
                {
                    "trigger": "filing_updated",
                    "invalidate": [
                        "filing:meta:{cik}:{accession}",
                        "filing:analysis:{cik}:{accession}",
                        "filing:signals:{cik}:{accession}",
                        "company:filings:{cik}",
                        "signal:summary:{cik}"
                    ]
                },
                {
                    "trigger": "company_data_updated",
                    "invalidate_pattern": "company:*:{cik}:*"
                }
            ]
        },
        {
            "name": "time_based_invalidation",
            "description": "Invalidate stale data based on age",
            "rules": [
                {
                    "pattern": "market:*",
                    "max_age": 300,  # 5 minutes
                    "check_interval": 60
                }
            ]
        },
        {
            "name": "manual_invalidation",
            "description": "Manual cache busting via API",
            "enabled": True,
            "api_endpoint": "/api/v1/cache/invalidate",
            "authentication": "required"
        }
    ]
}


# ============================================
# CACHE COMPRESSION
# ============================================

CACHE_COMPRESSION_CONFIG = {
    "enabled": True,
    "algorithm": "gzip",  # Options: gzip, lz4, zstd
    "level": 6,  # Compression level (1-9)
    "threshold": 1024,  # Only compress data > 1KB

    # Compression by key type
    "per_key_config": {
        "filing:text:*": {
            "enabled": True,
            "algorithm": "gzip",
            "level": 9  # High compression for large text
        },
        "filing:analysis:*": {
            "enabled": True,
            "algorithm": "gzip",
            "level": 6
        },
        "market:*": {
            "enabled": False  # Small, don't compress
        }
    }
}


# ============================================
# CACHE MONITORING
# ============================================

CACHE_MONITORING_CONFIG = {
    "metrics": [
        "hit_rate",
        "miss_rate",
        "eviction_rate",
        "memory_usage",
        "connection_count",
        "command_latency",
        "keys_count",
        "expired_keys",
        "keyspace_hits",
        "keyspace_misses"
    ],

    "alerts": [
        {
            "name": "low_hit_rate",
            "condition": "hit_rate < 0.95",
            "severity": "warning",
            "action": "notify_team"
        },
        {
            "name": "high_memory_usage",
            "condition": "memory_usage > 0.85",
            "severity": "critical",
            "action": ["notify_team", "increase_eviction"]
        },
        {
            "name": "high_latency",
            "condition": "p95_latency > 20",  # milliseconds
            "severity": "warning",
            "action": "investigate"
        },
        {
            "name": "connection_limit",
            "condition": "connection_count > 90",  # 90% of max
            "severity": "warning",
            "action": "notify_team"
        }
    ],

    "dashboards": [
        {
            "name": "cache_overview",
            "metrics": [
                "hit_rate_timeseries",
                "memory_usage_gauge",
                "command_latency_heatmap",
                "keys_by_prefix"
            ]
        }
    ]
}


# ============================================
# REDIS CLUSTER CONFIGURATION
# ============================================

REDIS_CLUSTER_CONFIG = {
    "enabled": True,
    "nodes": [
        {"host": "redis-node-1", "port": 6379},
        {"host": "redis-node-2", "port": 6379},
        {"host": "redis-node-3", "port": 6379}
    ],

    # Cluster settings
    "cluster_require_full_coverage": "no",
    "cluster_node_timeout": 15000,  # milliseconds
    "cluster_replica_validity_factor": 10,
    "cluster_migration_barrier": 1,

    # Replication
    "replication_factor": 2,  # 1 master + 1 replica per shard
    "min_replicas_to_write": 1,
    "min_replicas_max_lag": 10,  # seconds

    # Failover
    "cluster_replica_no_failover": "no",
    "cluster_allow_reads_when_down": "yes"
}


# ============================================
# OPTIMIZATION FUNCTIONS
# ============================================

def get_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Generate optimized cache key

    Args:
        prefix: Key prefix from CACHE_KEY_PREFIXES
        *args: Positional arguments for key
        **kwargs: Keyword arguments for key

    Returns:
        Formatted cache key
    """
    import hashlib
    import json

    # Get prefix
    key_prefix = CACHE_KEY_PREFIXES.get(prefix, prefix)

    # Build key parts
    parts = [key_prefix]
    parts.extend(str(arg) for arg in args)

    # Add sorted kwargs
    if kwargs:
        kwargs_str = json.dumps(kwargs, sort_keys=True)
        kwargs_hash = hashlib.md5(kwargs_str.encode()).hexdigest()[:8]
        parts.append(kwargs_hash)

    return ":".join(parts)


def get_ttl_for_key(key: str, context: Optional[Dict[str, Any]] = None) -> int:
    """
    Get appropriate TTL for cache key based on context

    Args:
        key: Cache key
        context: Additional context for TTL decision

    Returns:
        TTL in seconds
    """
    context = context or {}

    # Extract key prefix
    prefix = key.split(":")[0]

    # Map to TTL config
    ttl_config = CACHE_TTL_STRATEGY.get(prefix, {"default": 3600})

    # Check context for specific TTL
    if context.get("high_traffic"):
        return ttl_config.get("high_traffic", ttl_config["default"])
    elif context.get("historical"):
        return ttl_config.get("historical", ttl_config["default"])
    elif context.get("recent"):
        return ttl_config.get("recent", ttl_config["default"])

    return ttl_config["default"]


def get_optimization_summary() -> Dict[str, Any]:
    """Get summary of Redis optimizations"""
    return {
        "connection_pool": {
            "max_connections": REDIS_CONNECTION_CONFIG["max_connections"],
            "socket_keepalive": REDIS_CONNECTION_CONFIG["socket_keepalive"],
            "retry_enabled": REDIS_CONNECTION_CONFIG["retry_on_timeout"]
        },
        "server_config": {
            "maxmemory": REDIS_SERVER_CONFIG["maxmemory"],
            "eviction_policy": REDIS_SERVER_CONFIG["maxmemory_policy"],
            "io_threads": REDIS_SERVER_CONFIG["io_threads"]
        },
        "cache_strategies": {
            "key_prefixes": len(CACHE_KEY_PREFIXES),
            "ttl_strategies": len(CACHE_TTL_STRATEGY),
            "warming_enabled": CACHE_WARMING_CONFIG["enabled"],
            "compression_enabled": CACHE_COMPRESSION_CONFIG["enabled"]
        },
        "monitoring": {
            "metrics_count": len(CACHE_MONITORING_CONFIG["metrics"]),
            "alerts_configured": len(CACHE_MONITORING_CONFIG["alerts"])
        },
        "cluster": {
            "enabled": REDIS_CLUSTER_CONFIG["enabled"],
            "nodes": len(REDIS_CLUSTER_CONFIG["nodes"]),
            "replication_factor": REDIS_CLUSTER_CONFIG["replication_factor"]
        }
    }


if __name__ == "__main__":
    # Test cache key generation
    print("=== CACHE KEY EXAMPLES ===\n")

    filing_key = get_cache_key("FILING_METADATA", cik="0000789019", accession="0001564590-23-012345")
    print(f"Filing key: {filing_key}")

    prediction_key = get_cache_key("PREDICTION", filing_id="12345", model="sonnet")
    print(f"Prediction key: {prediction_key}")

    print("\n=== OPTIMIZATION SUMMARY ===\n")
    import json
    print(json.dumps(get_optimization_summary(), indent=2))
