# Redis Cache Architecture

## Overview

Redis 7.x serves as the primary cache layer and message broker for the SEC Latent platform, providing sub-millisecond response times and supporting real-time features.

## Architecture Diagram

```
┌─────────────────────── Application Layer ───────────────────────┐
│                                                                   │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                  │
│  │ Backend  │    │  Worker  │    │   Beat   │                  │
│  │ FastAPI  │    │  Celery  │    │ Scheduler│                  │
│  └────┬─────┘    └────┬─────┘    └────┬─────┘                  │
│       │               │               │                          │
└───────┼───────────────┼───────────────┼──────────────────────────┘
        │               │               │
        └───────────────┴───────────────┘
                        │
        ┌───────────────┴───────────────┐
        │                               │
┌───────▼────────┐              ┌───────▼────────┐
│  Redis Master  │◄─────────────┤ Redis Sentinel │
│     :6379      │  Monitoring  │     :26379     │
└───────┬────────┘              └────────────────┘
        │
        │ Async Replication
        │
┌───────┴────────────────────┐
│                             │
┌─────▼──────┐        ┌──────▼─────┐
│   Replica  │        │   Replica  │
│    :6379   │        │    :6379   │
└────────────┘        └────────────┘
```

## Use Cases

### 1. API Response Caching (Cache-Aside Pattern)

```python
# Pseudo-code for cache-aside pattern
def get_filing_analysis(filing_id: int) -> dict:
    # Try cache first
    cache_key = f"filing:analysis:{filing_id}"
    cached = redis.get(cache_key)

    if cached:
        return json.loads(cached)

    # Cache miss - query database
    analysis = db.query(Analysis).filter_by(filing_id=filing_id).first()

    # Store in cache with TTL
    redis.setex(cache_key, 3600, json.dumps(analysis))

    return analysis
```

### 2. Session Storage (Write-Through Pattern)

```python
# Store session data
def create_session(user_id: int, token: str) -> None:
    session_key = f"session:{token}"
    session_data = {
        "user_id": user_id,
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(days=7)).isoformat()
    }

    # Write to Redis (persistent)
    redis.setex(session_key, 604800, json.dumps(session_data))
```

### 3. Rate Limiting (Sliding Window)

```python
def check_rate_limit(api_key: str, limit: int = 100, window: int = 60) -> bool:
    key = f"ratelimit:{api_key}"
    current_time = int(time.time())

    # Remove old entries outside the window
    redis.zremrangebyscore(key, 0, current_time - window)

    # Count requests in current window
    request_count = redis.zcard(key)

    if request_count >= limit:
        return False

    # Add current request
    redis.zadd(key, {current_time: current_time})
    redis.expire(key, window)

    return True
```

### 4. Celery Message Broker

```python
# Celery configuration
CELERY_BROKER_URL = "redis://redis:6379/0"
CELERY_RESULT_BACKEND = "redis://redis:6379/0"

# Task queues
CELERY_TASK_ROUTES = {
    "tasks.extract_signals": {"queue": "high_priority"},
    "tasks.analyze_filing": {"queue": "medium_priority"},
    "tasks.update_index": {"queue": "low_priority"}
}
```

### 5. Real-Time Updates (Pub/Sub)

```python
# Publisher
def notify_filing_processed(filing_id: int) -> None:
    redis.publish(
        "filing:processed",
        json.dumps({"filing_id": filing_id, "timestamp": time.time()})
    )

# Subscriber
pubsub = redis.pubsub()
pubsub.subscribe("filing:processed")

for message in pubsub.listen():
    if message["type"] == "message":
        data = json.loads(message["data"])
        # Handle notification
```

## Configuration

### redis.conf

```conf
# Network
bind 0.0.0.0
port 6379
protected-mode yes
requirepass ${REDIS_PASSWORD}

# Persistence
save 900 1      # Save after 900s if at least 1 key changed
save 300 10     # Save after 300s if at least 10 keys changed
save 60 10000   # Save after 60s if at least 10000 keys changed

appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec

# Memory Management
maxmemory 2gb
maxmemory-policy allkeys-lru

# Performance
tcp-backlog 511
tcp-keepalive 300
timeout 300

# Replication
replica-read-only yes
replica-serve-stale-data yes
repl-diskless-sync no
repl-diskless-sync-delay 5

# Security
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command CONFIG "CONFIG_SECURE_COMMAND"

# Logging
loglevel notice
logfile "/var/log/redis/redis-server.log"

# Slow Log
slowlog-log-slower-than 10000
slowlog-max-len 128
```

### Redis Sentinel Configuration

**sentinel.conf**:
```conf
port 26379
sentinel monitor sec-latent-master redis-master 6379 2
sentinel auth-pass sec-latent-master ${REDIS_PASSWORD}
sentinel down-after-milliseconds sec-latent-master 5000
sentinel parallel-syncs sec-latent-master 1
sentinel failover-timeout sec-latent-master 10000
```

## High Availability Setup

### Redis Sentinel

```yaml
# docker-compose.yml addition
redis-master:
  image: redis:7-alpine
  command: redis-server /usr/local/etc/redis/redis.conf
  volumes:
    - ./config/redis/redis.conf:/usr/local/etc/redis/redis.conf
    - redis-master-data:/data
  networks:
    - sec-latent-network

redis-replica-1:
  image: redis:7-alpine
  command: redis-server --replicaof redis-master 6379 --requirepass ${REDIS_PASSWORD}
  depends_on:
    - redis-master
  networks:
    - sec-latent-network

redis-replica-2:
  image: redis:7-alpine
  command: redis-server --replicaof redis-master 6379 --requirepass ${REDIS_PASSWORD}
  depends_on:
    - redis-master
  networks:
    - sec-latent-network

redis-sentinel-1:
  image: redis:7-alpine
  command: redis-sentinel /usr/local/etc/redis/sentinel.conf
  volumes:
    - ./config/redis/sentinel.conf:/usr/local/etc/redis/sentinel.conf
  depends_on:
    - redis-master
  ports:
    - "26379:26379"
  networks:
    - sec-latent-network

redis-sentinel-2:
  image: redis:7-alpine
  command: redis-sentinel /usr/local/etc/redis/sentinel.conf
  volumes:
    - ./config/redis/sentinel.conf:/usr/local/etc/redis/sentinel.conf
  depends_on:
    - redis-master
  ports:
    - "26380:26379"
  networks:
    - sec-latent-network

redis-sentinel-3:
  image: redis:7-alpine
  command: redis-sentinel /usr/local/etc/redis/sentinel.conf
  volumes:
    - ./config/redis/sentinel.conf:/usr/local/etc/redis/sentinel.conf
  depends_on:
    - redis-master
  ports:
    - "26381:26379"
  networks:
    - sec-latent-network
```

### Application Configuration with Sentinel

```python
from redis.sentinel import Sentinel

# Connect via Sentinel
sentinel = Sentinel([
    ('sentinel-1', 26379),
    ('sentinel-2', 26379),
    ('sentinel-3', 26379)
], socket_timeout=0.1)

# Get master for writes
master = sentinel.master_for('sec-latent-master', password='${REDIS_PASSWORD}')

# Get slave for reads
slave = sentinel.slave_for('sec-latent-master', password='${REDIS_PASSWORD}')

# Write operation
master.set('key', 'value')

# Read operation
slave.get('key')
```

## Data Structures and Patterns

### 1. String (Simple Key-Value)

```python
# Cache API responses
redis.setex("filing:10-K:123", 3600, json.dumps(filing_data))

# Session tokens
redis.set("session:abc123", user_id, ex=604800)

# Counters
redis.incr("filing:processed:count")
```

### 2. Hash (Object Storage)

```python
# Store user profile
redis.hset("user:123", mapping={
    "name": "John Doe",
    "email": "john@example.com",
    "role": "analyst"
})

# Get specific field
redis.hget("user:123", "email")

# Get all fields
redis.hgetall("user:123")
```

### 3. List (Queue/Timeline)

```python
# Task queue
redis.lpush("queue:high_priority", json.dumps(task))
task = redis.brpop("queue:high_priority", timeout=5)

# Recent filings
redis.lpush("recent:filings", filing_id)
redis.ltrim("recent:filings", 0, 99)  # Keep last 100
```

### 4. Set (Unique Collection)

```python
# Unique companies processed today
redis.sadd("processed:companies:2025-10-19", "AAPL", "MSFT", "GOOGL")

# Check membership
redis.sismember("processed:companies:2025-10-19", "AAPL")

# Get all members
redis.smembers("processed:companies:2025-10-19")
```

### 5. Sorted Set (Leaderboard/Priority Queue)

```python
# Company rankings by signal strength
redis.zadd("rankings:signals", {
    "AAPL": 95.5,
    "MSFT": 92.3,
    "GOOGL": 89.7
})

# Top 10 companies
redis.zrevrange("rankings:signals", 0, 9, withscores=True)

# Rank of specific company
redis.zrevrank("rankings:signals", "AAPL")
```

### 6. HyperLogLog (Cardinality Estimation)

```python
# Unique visitors count
redis.pfadd("unique:visitors:2025-10-19", "user1", "user2", "user3")

# Get approximate count
redis.pfcount("unique:visitors:2025-10-19")

# Merge multiple days
redis.pfmerge("unique:visitors:week",
    "unique:visitors:2025-10-19",
    "unique:visitors:2025-10-20",
    "unique:visitors:2025-10-21"
)
```

## Cache Strategies

### Cache Invalidation

```python
class CacheManager:
    def __init__(self, redis_client):
        self.redis = redis_client

    def invalidate_filing(self, filing_id: int):
        """Invalidate all cache entries related to a filing"""
        patterns = [
            f"filing:{filing_id}:*",
            f"company:*:filings",
            "recent:filings"
        ]

        for pattern in patterns:
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)

    def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern"""
        keys = self.redis.keys(pattern)
        if keys:
            self.redis.delete(*keys)
```

### Cache Warming

```bash
#!/bin/bash
# scripts/warm-cache.sh

# Warm cache with most accessed filings
psql -d sec_latent -c "
    SELECT filing_id, accession_number
    FROM filings
    WHERE filing_date >= NOW() - INTERVAL '30 days'
    ORDER BY filing_date DESC
    LIMIT 1000
" | while read filing_id accession; do
    curl "https://api.sec-latent.com/filings/${filing_id}" \
        -H "X-Cache-Warm: true" \
        > /dev/null 2>&1
done
```

### Cache Stampede Prevention

```python
import hashlib
import time

def get_with_lock(key: str, fetch_func, ttl: int = 3600) -> Any:
    """Prevent cache stampede with distributed lock"""

    # Try to get from cache
    value = redis.get(key)
    if value:
        return json.loads(value)

    # Acquire lock
    lock_key = f"lock:{key}"
    lock_value = hashlib.md5(str(time.time()).encode()).hexdigest()

    # Try to acquire lock with 10 second TTL
    acquired = redis.set(lock_key, lock_value, nx=True, ex=10)

    if acquired:
        try:
            # Fetch data
            value = fetch_func()

            # Store in cache
            redis.setex(key, ttl, json.dumps(value))

            return value
        finally:
            # Release lock (only if we still own it)
            script = """
                if redis.call("get", KEYS[1]) == ARGV[1] then
                    return redis.call("del", KEYS[1])
                else
                    return 0
                end
            """
            redis.eval(script, 1, lock_key, lock_value)
    else:
        # Wait for lock to be released, then retry
        for _ in range(10):
            time.sleep(0.1)
            value = redis.get(key)
            if value:
                return json.loads(value)

        # Fallback: fetch without cache
        return fetch_func()
```

## Monitoring

### Redis Metrics

```python
# Get Redis info
info = redis.info()

metrics = {
    "connected_clients": info["connected_clients"],
    "used_memory": info["used_memory"],
    "used_memory_human": info["used_memory_human"],
    "used_memory_peak": info["used_memory_peak"],
    "mem_fragmentation_ratio": info["mem_fragmentation_ratio"],
    "total_commands_processed": info["total_commands_processed"],
    "instantaneous_ops_per_sec": info["instantaneous_ops_per_sec"],
    "keyspace_hits": info["keyspace_hits"],
    "keyspace_misses": info["keyspace_misses"],
    "evicted_keys": info["evicted_keys"],
    "expired_keys": info["expired_keys"]
}

# Calculate cache hit rate
hit_rate = (
    metrics["keyspace_hits"] /
    (metrics["keyspace_hits"] + metrics["keyspace_misses"])
) * 100
```

### Prometheus Exporter

**docker-compose.yml** addition:
```yaml
redis-exporter:
  image: oliver006/redis_exporter:latest
  environment:
    REDIS_ADDR: redis://redis:6379
    REDIS_PASSWORD: ${REDIS_PASSWORD}
  ports:
    - "9121:9121"
  networks:
    - sec-latent-network
```

### Slow Log Analysis

```bash
# Get slow log entries
redis-cli SLOWLOG GET 10

# Example output:
# 1) 1) (integer) 1
#    2) (integer) 1634567890
#    3) (integer) 12000  # microseconds
#    4) 1) "KEYS"
#       2) "filing:*"
```

## Performance Optimization

### Pipeline Batching

```python
# Without pipeline (N round trips)
for i in range(1000):
    redis.set(f"key:{i}", f"value:{i}")

# With pipeline (1 round trip)
pipe = redis.pipeline()
for i in range(1000):
    pipe.set(f"key:{i}", f"value:{i}")
pipe.execute()
```

### Connection Pooling

```python
from redis import ConnectionPool

# Create connection pool
pool = ConnectionPool(
    host='redis',
    port=6379,
    password='${REDIS_PASSWORD}',
    db=0,
    max_connections=50,
    socket_timeout=5,
    socket_connect_timeout=5,
    socket_keepalive=True,
    health_check_interval=30
)

# Use pool
redis_client = redis.Redis(connection_pool=pool)
```

### Lua Scripts

```python
# Atomic rate limiting with Lua
rate_limit_script = """
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local current = tonumber(ARGV[3])

redis.call('ZREMRANGEBYSCORE', key, 0, current - window)
local count = redis.call('ZCARD', key)

if count < limit then
    redis.call('ZADD', key, current, current)
    redis.call('EXPIRE', key, window)
    return 1
else
    return 0
end
"""

# Register script
rate_limit_sha = redis.script_load(rate_limit_script)

# Execute script
allowed = redis.evalsha(
    rate_limit_sha,
    1,  # Number of keys
    "ratelimit:api_key",  # Key
    100,  # Limit
    60,  # Window
    int(time.time())  # Current time
)
```

## Security

### Authentication

```conf
# redis.conf
requirepass ${REDIS_PASSWORD}
```

```python
# Application connection
redis_client = redis.Redis(
    host='redis',
    port=6379,
    password=os.getenv('REDIS_PASSWORD'),
    ssl=True,  # Use TLS in production
    ssl_cert_reqs='required'
)
```

### ACL (Access Control Lists)

```redis
# Create read-only user
ACL SETUSER readonly on >readonly_password ~* -@all +@read

# Create write user for specific patterns
ACL SETUSER writer on >writer_password ~cache:* +@write +@read

# Application-specific user
ACL SETUSER celery on >celery_password ~queue:* ~result:* +@write +@read +@pubsub
```

### Encryption

```python
# Encrypt sensitive data before caching
from cryptography.fernet import Fernet

cipher = Fernet(os.getenv('CACHE_ENCRYPTION_KEY'))

def cache_sensitive(key: str, data: dict, ttl: int = 3600):
    encrypted = cipher.encrypt(json.dumps(data).encode())
    redis.setex(key, ttl, encrypted)

def get_sensitive(key: str) -> dict:
    encrypted = redis.get(key)
    if encrypted:
        decrypted = cipher.decrypt(encrypted)
        return json.loads(decrypted)
    return None
```

## Backup and Recovery

### RDB Snapshots

```bash
# Manual backup
redis-cli --rdb /backups/redis/dump.rdb

# Automated backup script
#!/bin/bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
redis-cli BGSAVE
sleep 10
cp /var/lib/redis/dump.rdb /backups/redis/dump_${TIMESTAMP}.rdb
```

### AOF Backups

```bash
# Backup AOF file
cp /var/lib/redis/appendonly.aof /backups/redis/appendonly_${TIMESTAMP}.aof
```

### Restore Procedure

```bash
# Stop Redis
systemctl stop redis

# Restore RDB
cp /backups/redis/dump_20251019_020000.rdb /var/lib/redis/dump.rdb

# Or restore AOF
cp /backups/redis/appendonly_20251019_020000.aof /var/lib/redis/appendonly.aof

# Start Redis
systemctl start redis
```

## Capacity Planning

### Current Usage
- Memory: 2 GB
- Keys: 10 million
- Ops/sec: 10,000
- Network I/O: 100 MB/s

### 12-Month Projection
- Memory: 8 GB
- Keys: 50 million
- Ops/sec: 50,000
- Network I/O: 500 MB/s

### Scaling Strategy
1. **0-3 months**: Vertical scaling (increase memory)
2. **3-6 months**: Add read replicas (3 replicas)
3. **6-12 months**: Redis Cluster with sharding
4. **12+ months**: Multi-region deployment

## Redis Cluster (Future)

```
┌──────────────── Redis Cluster ────────────────┐
│                                                │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐       │
│  │Master 1 │  │Master 2 │  │Master 3 │       │
│  │Hash Slot│  │Hash Slot│  │Hash Slot│       │
│  │0-5461   │  │5462-10922│ │10923-16383│      │
│  └────┬────┘  └────┬────┘  └────┬────┘       │
│       │            │            │             │
│  ┌────▼────┐  ┌────▼────┐  ┌────▼────┐       │
│  │Replica 1│  │Replica 2│  │Replica 3│       │
│  └─────────┘  └─────────┘  └─────────┘       │
│                                                │
└────────────────────────────────────────────────┘
```

**redis-cluster.conf**:
```conf
port 7000
cluster-enabled yes
cluster-config-file nodes.conf
cluster-node-timeout 5000
appendonly yes
```

## Troubleshooting

### High Memory Usage

```bash
# Find largest keys
redis-cli --bigkeys

# Memory doctor
redis-cli --memkeys

# Analyze memory usage
redis-cli MEMORY DOCTOR
```

### Slow Performance

```bash
# Check slow log
redis-cli SLOWLOG GET 20

# Monitor commands in real-time
redis-cli MONITOR

# Check latency
redis-cli --latency
```

### Connection Issues

```bash
# Check connections
redis-cli CLIENT LIST

# Kill specific client
redis-cli CLIENT KILL <client-address>
```
