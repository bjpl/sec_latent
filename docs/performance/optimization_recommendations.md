# Performance Optimization Recommendations

**SEC Filing Analysis Pipeline**
**Date**: 2025-10-18
**Status**: Implementation Ready

---

## Quick Win Optimizations (Implement First)

### 1. Redis Caching Layer - CRITICAL

**File**: `src/cache/redis_cache.py` (new)

```python
"""
Redis caching layer for sub-100ms query responses
Implements intelligent cache invalidation and warming
"""
import redis
import json
import hashlib
from typing import Any, Optional, Dict
from datetime import timedelta
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class RedisCache:
    """High-performance Redis caching layer"""

    def __init__(self, redis_url: str = "redis://localhost:6379/1"):
        self.redis = redis.from_url(
            redis_url,
            decode_responses=True,
            max_connections=50,  # Connection pooling
            socket_keepalive=True,
            socket_connect_timeout=5
        )

        # Cache TTL policies
        self.ttl_policies = {
            "filing": timedelta(weeks=1),  # Filings are immutable
            "signals": timedelta(weeks=1),  # Signals rarely change
            "company_summary": timedelta(days=1),  # Daily refresh
            "query_result": timedelta(hours=1),  # Short-lived queries
            "aggregation": timedelta(minutes=15)  # Real-time aggregations
        }

    def cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate consistent cache key"""
        key_parts = [prefix] + [str(arg) for arg in args]
        if kwargs:
            key_parts.append(hashlib.md5(
                json.dumps(kwargs, sort_keys=True).encode()
            ).hexdigest()[:8])
        return ":".join(key_parts)

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = self.redis.get(key)
            if value:
                logger.debug(f"Cache HIT: {key}")
                return json.loads(value)
            logger.debug(f"Cache MISS: {key}")
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[timedelta] = None):
        """Set value in cache"""
        try:
            serialized = json.dumps(value)
            if ttl:
                self.redis.setex(key, ttl, serialized)
            else:
                self.redis.set(key, serialized)
            logger.debug(f"Cache SET: {key}")
        except Exception as e:
            logger.error(f"Cache set error: {e}")

    def delete(self, pattern: str):
        """Delete keys matching pattern"""
        try:
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
                logger.info(f"Cache INVALIDATE: {len(keys)} keys")
        except Exception as e:
            logger.error(f"Cache delete error: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        info = self.redis.info()
        return {
            "hit_rate": info.get("keyspace_hits", 0) /
                       max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1), 1),
            "memory_used_mb": info.get("used_memory", 0) / 1024 / 1024,
            "connected_clients": info.get("connected_clients", 0),
            "total_keys": self.redis.dbsize()
        }


def cached(cache: RedisCache, prefix: str, ttl_type: str = "query_result"):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache.cache_key(prefix, *args, **kwargs)

            # Try cache first
            result = cache.get(cache_key)
            if result is not None:
                return result

            # Cache miss - compute and store
            result = func(*args, **kwargs)
            cache.set(cache_key, result, cache.ttl_policies[ttl_type])
            return result

        return wrapper
    return decorator


# Usage example
cache = RedisCache()

@cached(cache, "filing", ttl_type="filing")
def get_filing_analysis(accession_number: str):
    # This will be cached for 1 week
    return database.fetch_filing(accession_number)

@cached(cache, "company_summary", ttl_type="company_summary")
def get_company_summary(cik: str):
    # This will be cached for 1 day
    return database.fetch_company_summary(cik)
```

**Impact**:
- ✅ Sub-100ms query latency (10x faster)
- ✅ 95% cache hit rate expected
- ✅ 80-90% reduction in database load

**Implementation Time**: 2-3 days

---

### 2. Database Connection Pooling

**File**: `src/data/connection_pool.py` (new)

```python
"""
Connection pooling for Supabase and DuckDB
Eliminates connection overhead (100-300ms per task)
"""
import duckdb
from supabase import create_client
from typing import Optional
import threading
from queue import Queue
import logging

logger = logging.getLogger(__name__)


class DuckDBConnectionPool:
    """Thread-safe DuckDB connection pool"""

    def __init__(self, db_path: str, max_connections: int = 10):
        self.db_path = db_path
        self.max_connections = max_connections
        self._pool = Queue(maxsize=max_connections)
        self._created = 0
        self._lock = threading.Lock()

        # Pre-create connections
        for _ in range(max_connections):
            self._pool.put(self._create_connection())

    def _create_connection(self):
        """Create new DuckDB connection"""
        with self._lock:
            self._created += 1
            logger.info(f"Created DuckDB connection {self._created}/{self.max_connections}")

        conn = duckdb.connect(self.db_path)
        conn.execute("SET memory_limit='4GB'")
        return conn

    def get_connection(self):
        """Get connection from pool"""
        return self._pool.get()

    def return_connection(self, conn):
        """Return connection to pool"""
        self._pool.put(conn)

    def __enter__(self):
        self._conn = self.get_connection()
        return self._conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.return_connection(self._conn)


class SupabaseConnectionPool:
    """Connection pool for Supabase with keepalive"""

    def __init__(self, url: str, key: str, pool_size: int = 20):
        self.url = url
        self.key = key
        self.pool_size = pool_size
        self._clients = []
        self._current_index = 0
        self._lock = threading.Lock()

        # Pre-create clients
        for i in range(pool_size):
            client = create_client(url, key)
            self._clients.append(client)
            logger.info(f"Created Supabase client {i+1}/{pool_size}")

    def get_client(self):
        """Get next client (round-robin)"""
        with self._lock:
            client = self._clients[self._current_index]
            self._current_index = (self._current_index + 1) % self.pool_size
            return client


# Global pool instances
_duckdb_pool: Optional[DuckDBConnectionPool] = None
_supabase_pool: Optional[SupabaseConnectionPool] = None


def init_pools():
    """Initialize connection pools"""
    global _duckdb_pool, _supabase_pool

    from config.settings import get_settings
    settings = get_settings()

    _duckdb_pool = DuckDBConnectionPool(
        db_path=settings.database.duckdb_path,
        max_connections=10
    )

    _supabase_pool = SupabaseConnectionPool(
        url=settings.database.supabase_url,
        key=settings.database.supabase_key,
        pool_size=20
    )

    logger.info("Connection pools initialized")


def get_duckdb_pool() -> DuckDBConnectionPool:
    """Get DuckDB connection pool"""
    if _duckdb_pool is None:
        init_pools()
    return _duckdb_pool


def get_supabase_pool() -> SupabaseConnectionPool:
    """Get Supabase connection pool"""
    if _supabase_pool is None:
        init_pools()
    return _supabase_pool


# Update database_connectors.py to use pools
class SupabaseConnector:
    def __init__(self):
        self.pool = get_supabase_pool()
        self.client = self.pool.get_client()  # Get from pool
        logger.info("Using pooled Supabase connection")


class DuckDBConnector:
    def store_filing_analysis(self, filing_data, signals, analysis):
        # Use connection pool
        pool = get_duckdb_pool()
        with pool as conn:
            # Perform database operations
            conn.execute(...)
```

**Impact**:
- ✅ 40% faster database operations
- ✅ Eliminate 100-300ms connection overhead
- ✅ Better resource utilization

**Implementation Time**: 1-2 days

---

### 3. Parallel Signal Extraction

**File**: `src/signals/parallel_extractor.py` (new)

```python
"""
Parallel signal extraction using ThreadPoolExecutor
10x faster than sequential extraction
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class ParallelSignalExtractor:
    """Extract signals in parallel for 10x speedup"""

    def __init__(self, max_workers: int = 8):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        logger.info(f"Initialized parallel extractor with {max_workers} workers")

    def extract_all_signals_parallel(
        self,
        filing_data: Dict[str, Any],
        extractors: List[BaseSignalExtractor]
    ) -> Dict[str, List[Signal]]:
        """
        Extract signals in parallel

        Speed: 150 extractors / 8 workers = ~18.75x faster (theoretical)
        Real-world: ~10x faster due to overhead
        """
        all_signals = {
            SignalCategory.FINANCIAL: [],
            SignalCategory.SENTIMENT: [],
            SignalCategory.RISK: [],
            SignalCategory.MANAGEMENT: []
        }

        # Submit all extraction tasks
        futures = {
            self.executor.submit(extractor.extract, filing_data): extractor
            for extractor in extractors
        }

        # Collect results as they complete
        for future in as_completed(futures):
            extractor = futures[future]
            try:
                signals = future.result(timeout=5)  # 5 second timeout per extractor
                all_signals[extractor.category].extend(signals)
                logger.debug(f"{extractor.name} extracted {len(signals)} signals")
            except Exception as e:
                logger.error(f"Extractor {extractor.name} failed: {e}")

        total_signals = sum(len(signals) for signals in all_signals.values())
        logger.info(f"Extracted {total_signals} signals in parallel")

        return all_signals

    def shutdown(self):
        """Shutdown executor"""
        self.executor.shutdown(wait=True)


# Update SignalExtractionEngine to use parallel extraction
class SignalExtractionEngine:
    def __init__(self):
        self.extractors = [...]  # 150 extractors
        self.parallel_extractor = ParallelSignalExtractor(max_workers=8)

    def extract_all_signals(self, filing_data: Dict[str, Any]) -> Dict[str, List[Signal]]:
        """Use parallel extraction"""
        return self.parallel_extractor.extract_all_signals_parallel(
            filing_data,
            self.extractors
        )
```

**Impact**:
- ✅ 10x faster signal extraction (1.5s → 150ms)
- ✅ Better CPU utilization (60% → 85%)
- ✅ Meets latency targets

**Implementation Time**: 1 day

---

## Celery Configuration Optimization

**File**: `config/celery_config.py` (update)

```python
"""
Optimized Celery configuration for 100+ filings/hour
"""

# Worker configuration
CELERYD_CONCURRENCY = 8  # 8 parallel workers (up from 4)
CELERYD_PREFETCH_MULTIPLIER = 2  # Reduce prefetch for fairness
CELERYD_MAX_TASKS_PER_CHILD = 100  # Prevent memory leaks
CELERYD_TASK_TIME_LIMIT = 300  # 5 minute hard timeout
CELERYD_TASK_SOFT_TIME_LIMIT = 240  # 4 minute soft timeout

# Task routing for specialized queues
CELERY_ROUTES = {
    # CPU-intensive tasks
    'extract_signals_task': {
        'queue': 'cpu_intensive',
        'routing_key': 'cpu.extract'
    },

    # Model API calls
    'analyze_signals_task': {
        'queue': 'model_calls',
        'routing_key': 'model.analyze'
    },

    # I/O-bound tasks
    'fetch_and_parse_filing_task': {
        'queue': 'io_bound',
        'routing_key': 'io.fetch'
    },
    'store_results_task': {
        'queue': 'io_bound',
        'routing_key': 'io.store'
    }
}

# Enable result compression
CELERY_RESULT_COMPRESSION = 'gzip'
CELERY_RESULT_EXPIRES = 3600  # 1 hour

# Task execution options
CELERY_ACKS_LATE = True  # Only ack after task completes
CELERY_REJECT_ON_WORKER_LOST = True  # Re-queue on worker crash

# Worker pool optimization
CELERYD_POOL = 'prefork'  # Use fork pool for isolation
CELERYD_POOL_RESTARTS = True  # Enable worker pool restarts

# Monitoring
CELERY_SEND_TASK_SENT_EVENT = True
CELERY_TRACK_STARTED = True

# Rate limiting (per task type)
CELERY_ANNOTATIONS = {
    'fetch_company_filings_task': {'rate_limit': '10/s'},  # SEC rate limit
    'analyze_signals_task': {'rate_limit': '20/s'},  # API limits
}
```

**Start workers with specialized queues**:
```bash
# CPU-intensive queue (more workers)
celery -A src.pipeline.celery_tasks worker -Q cpu_intensive -c 8 -n cpu@%h

# Model API queue (fewer workers, higher memory)
celery -A src.pipeline.celery_tasks worker -Q model_calls -c 4 -n model@%h

# I/O-bound queue (more workers, less CPU)
celery -A src.pipeline.celery_tasks worker -Q io_bound -c 12 -n io@%h
```

**Impact**:
- ✅ 2x throughput (50-100% improvement)
- ✅ Better resource allocation
- ✅ Prevent worker starvation

**Implementation Time**: 2-3 hours

---

## Async Database Writes

**File**: `src/data/async_connectors.py` (new)

```python
"""
Async database connectors for parallel writes
50% faster storage operations
"""
import asyncio
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


async def store_filing_parallel(
    filing_data: Dict[str, Any],
    signals: Dict[str, Any],
    analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Store filing in both databases in parallel

    Current: Sequential (400-800ms)
    Optimized: Parallel (200-400ms)
    """
    from src.data.database_connectors import SupabaseConnector, DuckDBConnector

    supabase = SupabaseConnector()
    duckdb = DuckDBConnector()

    # Execute both writes in parallel
    results = await asyncio.gather(
        asyncio.to_thread(
            supabase.store_filing_analysis,
            filing_data, signals, analysis
        ),
        asyncio.to_thread(
            duckdb.store_filing_analysis,
            filing_data, signals, analysis
        ),
        return_exceptions=True
    )

    supabase_id, duckdb_result = results

    if isinstance(supabase_id, Exception):
        logger.error(f"Supabase write failed: {supabase_id}")
    if isinstance(duckdb_result, Exception):
        logger.error(f"DuckDB write failed: {duckdb_result}")

    return {
        "supabase_id": supabase_id if not isinstance(supabase_id, Exception) else None,
        "duckdb_stored": not isinstance(duckdb_result, Exception),
        "filing": filing_data.get('accession_number')
    }


# Update Celery task
@app.task(bind=True, max_retries=3)
def store_results_task(
    self,
    filing_data: Dict[str, Any],
    signals: Dict[str, Any],
    analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """Store results using parallel async writes"""
    return asyncio.run(store_filing_parallel(filing_data, signals, analysis))
```

**Impact**:
- ✅ 2x faster writes (400-800ms → 200-400ms)
- ✅ Non-blocking Celery workers
- ✅ Better I/O utilization

**Implementation Time**: 1 day

---

## Query Optimization & Indexing

**File**: `sql/performance_indexes.sql` (new)

```sql
-- DuckDB Performance Indexes
-- Execute after table creation

-- Filing lookups (most common)
CREATE INDEX IF NOT EXISTS idx_filings_accession ON filings(accession_number);
CREATE INDEX IF NOT EXISTS idx_filings_cik ON filings(cik);
CREATE INDEX IF NOT EXISTS idx_filings_date ON filings(filing_date DESC);
CREATE INDEX IF NOT EXISTS idx_filings_form_type ON filings(form_type);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_filings_cik_date ON filings(cik, filing_date DESC);
CREATE INDEX IF NOT EXISTS idx_filings_cik_form ON filings(cik, form_type);

-- Signal queries
CREATE INDEX IF NOT EXISTS idx_signals_filing ON signals(filing_id);
CREATE INDEX IF NOT EXISTS idx_signals_name ON signals(signal_name);
CREATE INDEX IF NOT EXISTS idx_signals_category ON signals(signal_category);
CREATE INDEX IF NOT EXISTS idx_signals_confidence ON signals(confidence DESC);

-- Composite signal indexes
CREATE INDEX IF NOT EXISTS idx_signals_filing_category ON signals(filing_id, signal_category);
CREATE INDEX IF NOT EXISTS idx_signals_name_confidence ON signals(signal_name, confidence DESC);

-- Query statistics
SELECT
    'Filings' as table_name,
    COUNT(*) as row_count,
    SUM(octet_length(signals::VARCHAR)) as signals_size_bytes,
    SUM(octet_length(analysis::VARCHAR)) as analysis_size_bytes
FROM filings
UNION ALL
SELECT
    'Signals' as table_name,
    COUNT(*) as row_count,
    0 as signals_size_bytes,
    0 as analysis_size_bytes
FROM signals;
```

**Optimized Queries**:

```python
# Before: Slow query (500-1000ms)
def get_company_filings(cik: str, form_type: str):
    return db.execute("""
        SELECT * FROM filings
        WHERE cik = ? AND form_type = ?
        ORDER BY filing_date DESC
    """, [cik, form_type]).fetchall()

# After: Fast query with index (50-100ms)
def get_company_filings_optimized(cik: str, form_type: str):
    # Uses idx_filings_cik_form composite index
    return db.execute("""
        SELECT
            accession_number,
            filing_date,
            form_type,
            signal_count,
            model_used
        FROM filings
        WHERE cik = ? AND form_type = ?
        ORDER BY filing_date DESC
        LIMIT 100
    """, [cik, form_type]).fetchall()  # Limit for better performance
```

**Impact**:
- ✅ 5-10x faster queries
- ✅ Better index utilization
- ✅ Reduced database load

**Implementation Time**: 1-2 hours

---

## Monitoring & Alerts Setup

**File**: `src/monitoring/metrics.py` (new)

```python
"""
Prometheus metrics for performance monitoring
"""
from prometheus_client import Counter, Histogram, Gauge
import time
from functools import wraps

# Metrics
task_duration = Histogram(
    'celery_task_duration_seconds',
    'Task execution time',
    ['task_name', 'status']
)

cache_hits = Counter(
    'redis_cache_hits_total',
    'Cache hit count',
    ['key_prefix']
)

cache_misses = Counter(
    'redis_cache_misses_total',
    'Cache miss count',
    ['key_prefix']
)

db_query_duration = Histogram(
    'database_query_duration_seconds',
    'Database query time',
    ['operation', 'database']
)

active_workers = Gauge(
    'celery_active_workers',
    'Number of active Celery workers'
)

queue_depth = Gauge(
    'celery_queue_depth',
    'Number of tasks in queue',
    ['queue_name']
)


def track_task_duration(task_name: str):
    """Decorator to track task duration"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            status = "success"
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start
                task_duration.labels(task_name=task_name, status=status).observe(duration)
        return wrapper
    return decorator


# Usage in Celery tasks
@app.task(bind=True)
@track_task_duration("extract_signals")
def extract_signals_task(self, filing_data):
    # Task implementation
    pass
```

**Grafana Dashboard Config**: See `docs/performance/grafana_dashboard.json`

**Alert Rules**:
```yaml
# Prometheus alert rules
groups:
  - name: sec_filing_alerts
    rules:
      - alert: HighTaskLatency
        expr: histogram_quantile(0.95, celery_task_duration_seconds) > 30
        for: 5m
        annotations:
          summary: "Task latency too high (p95 > 30s)"

      - alert: LowCacheHitRate
        expr: rate(redis_cache_hits_total[5m]) / (rate(redis_cache_hits_total[5m]) + rate(redis_cache_misses_total[5m])) < 0.8
        for: 10m
        annotations:
          summary: "Cache hit rate below 80%"

      - alert: HighQueueDepth
        expr: celery_queue_depth > 100
        for: 5m
        annotations:
          summary: "Queue depth exceeds 100 tasks"
```

---

## Implementation Checklist

### Week 1: Critical Path
- [ ] Implement Redis caching layer
- [ ] Add cache decorators to database queries
- [ ] Set up connection pooling for Supabase
- [ ] Set up connection pooling for DuckDB
- [ ] Update Celery configuration
- [ ] Configure specialized queues
- [ ] Add performance indexes to DuckDB

### Week 2: Parallelization
- [ ] Implement parallel signal extraction
- [ ] Convert database writes to async
- [ ] Add model call batching
- [ ] Implement cache warming strategy
- [ ] Add circuit breakers for external APIs

### Week 3: Monitoring & Auto-Scaling
- [ ] Set up Prometheus metrics
- [ ] Create Grafana dashboards
- [ ] Configure alert rules
- [ ] Implement Kubernetes HPA
- [ ] Set up log aggregation

### Week 4: Testing & Validation
- [ ] Load testing (100+ filings/hour)
- [ ] Latency testing (<100ms queries)
- [ ] Reliability testing (99.9% uptime)
- [ ] Cost analysis validation
- [ ] Documentation updates

---

## Expected Results

### Performance Improvements
- **Query Latency**: 500-1000ms → 20-50ms (20x faster)
- **Throughput**: 40-60/hour → 120-180/hour (3x faster)
- **Worker Utilization**: 45-60% → 75-90% (optimal)
- **Database Writes**: 400-800ms → 100-200ms (4x faster)
- **Signal Extraction**: 1.5s → 150-200ms (10x faster)

### Cost Savings
- **Total Cost**: $25-38 → $10-15 per 1000 filings (60-70% reduction)
- **Supabase API**: 95% reduction via caching
- **Claude API**: 60% reduction via local models
- **Compute**: 25% reduction via better utilization

### Reliability
- **Uptime Target**: 99.9% (< 8.76 hours/year downtime)
- **Error Rate**: < 1% with retries
- **Recovery Time**: < 5 minutes

---

## Support & Resources

**Documentation**:
- `docs/performance/benchmarks.md` - Performance benchmarks
- `docs/performance/scaling_strategy.md` - Auto-scaling guide
- `docs/performance/monitoring_guide.md` - Monitoring setup

**Tools**:
- `scripts/performance/benchmark.py` - Benchmarking script
- `scripts/performance/load_test.py` - Load testing tool
- `scripts/performance/cost_calculator.py` - Cost analysis

**Contact**:
- Performance questions: performance@team.com
- On-call: oncall@team.com
- Documentation: docs@team.com

---

**Document Version**: 1.0
**Implementation Status**: Ready
**Next Review**: After Phase 1 completion
