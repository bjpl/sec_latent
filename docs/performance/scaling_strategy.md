# Auto-Scaling Strategy for SEC Filing Analysis Pipeline

**Target**: 100+ filings/hour with 99.9% reliability
**Date**: 2025-10-18

---

## Scaling Architecture

### Component Scaling Matrix

| Component | Min Replicas | Max Replicas | Scale Trigger | Scale Metric |
|-----------|--------------|--------------|---------------|--------------|
| Celery Workers (CPU) | 4 | 20 | Queue depth > 50 | Task backlog |
| Celery Workers (I/O) | 8 | 30 | Worker CPU > 80% | CPU utilization |
| Celery Workers (Model) | 2 | 10 | Model queue > 20 | API latency |
| Redis Cache | 1 | 3 | Memory > 80% | Memory usage |
| DuckDB Readers | 2 | 8 | Query latency > 500ms | Query time |

---

## Horizontal Scaling Triggers

### Celery Worker Scaling

**Scale UP Conditions**:
```python
def should_scale_up() -> bool:
    """Determine if we need more workers"""

    # Check queue depth
    queue_depth = celery.inspect().active_queues()
    if any(q['pending_tasks'] > 50 for q in queue_depth.values()):
        return True

    # Check worker CPU utilization
    worker_stats = celery.inspect().stats()
    avg_cpu = sum(w['rusage']['cpu_percent'] for w in worker_stats.values()) / len(worker_stats)
    if avg_cpu > 85:
        return True

    # Check task latency (p95)
    p95_latency = get_task_latency_p95()
    if p95_latency > 30:  # seconds
        return True

    # Check throughput vs target
    current_throughput = get_filings_per_hour()
    if current_throughput < 100 and queue_depth['total'] > 20:
        return True

    return False


# Scale up policy
SCALE_UP_POLICY = {
    "cooldown": 60,  # seconds
    "increment": 2,  # Add 2 workers at a time
    "max_scale_per_hour": 10  # Maximum scaling events per hour
}
```

**Scale DOWN Conditions**:
```python
def should_scale_down() -> bool:
    """Determine if we can reduce workers"""

    # Check queue depth (sustained low for 10 min)
    queue_depth = celery.inspect().active_queues()
    if all(q['pending_tasks'] < 10 for q in queue_depth.values()):
        if sustained_for_minutes(lambda: queue_depth['total'] < 10, minutes=10):
            return True

    # Check worker CPU (sustained low for 10 min)
    worker_stats = celery.inspect().stats()
    avg_cpu = sum(w['rusage']['cpu_percent'] for w in worker_stats.values()) / len(worker_stats)
    if avg_cpu < 30:
        if sustained_for_minutes(lambda: avg_cpu < 30, minutes=10):
            return True

    return False


# Scale down policy
SCALE_DOWN_POLICY = {
    "cooldown": 300,  # 5 minutes
    "decrement": 1,  # Remove 1 worker at a time
    "min_replicas": 4  # Never go below 4 workers
}
```

---

## Kubernetes HPA Configuration

### Celery Worker HPA

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: celery-worker-cpu-hpa
  namespace: sec-filing
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: celery-worker-cpu
  minReplicas: 4
  maxReplicas: 20
  metrics:
  # CPU-based scaling
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70

  # Custom metric: Queue depth
  - type: Pods
    pods:
      metric:
        name: celery_queue_depth
      target:
        type: AverageValue
        averageValue: "50"

  # Custom metric: Task latency
  - type: Pods
    pods:
      metric:
        name: celery_task_latency_p95
      target:
        type: AverageValue
        averageValue: "20"  # 20 seconds

  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 50  # Scale up by 50% of current replicas
        periodSeconds: 60
      - type: Pods
        value: 2  # Or add 2 pods
        periodSeconds: 60
      selectPolicy: Max  # Use the higher of the two policies

    scaleDown:
      stabilizationWindowSeconds: 300  # 5 min stabilization
      policies:
      - type: Percent
        value: 25  # Scale down by 25%
        periodSeconds: 60
      - type: Pods
        value: 1  # Or remove 1 pod
        periodSeconds: 60
      selectPolicy: Min  # Use the lower of the two policies
---
# I/O Worker HPA (different thresholds)
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: celery-worker-io-hpa
  namespace: sec-filing
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: celery-worker-io
  minReplicas: 8
  maxReplicas: 30
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 60  # Lower threshold for I/O workers

  - type: Pods
    pods:
      metric:
        name: celery_io_queue_depth
      target:
        type: AverageValue
        averageValue: "100"  # Higher capacity for I/O
```

---

## Redis Scaling Strategy

### Vertical Scaling (Memory)

```yaml
# Redis deployment with memory-based scaling
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis-cache
spec:
  replicas: 1
  template:
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        resources:
          requests:
            memory: "4Gi"
            cpu: "1000m"
          limits:
            memory: "8Gi"
            cpu: "2000m"
        command:
        - redis-server
        - --maxmemory 7gb
        - --maxmemory-policy allkeys-lru
        - --appendonly yes
        - --save 900 1
        - --save 300 10
```

### Redis Sentinel (High Availability)

```yaml
# Redis Sentinel for automatic failover
apiVersion: v1
kind: ConfigMap
metadata:
  name: redis-sentinel-config
data:
  sentinel.conf: |
    sentinel monitor sec-redis redis-master 6379 2
    sentinel down-after-milliseconds sec-redis 5000
    sentinel parallel-syncs sec-redis 1
    sentinel failover-timeout sec-redis 10000
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis-sentinel
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: sentinel
        image: redis:7-alpine
        command: ["redis-sentinel"]
        args: ["/config/sentinel.conf"]
        volumeMounts:
        - name: config
          mountPath: /config
      volumes:
      - name: config
        configMap:
          name: redis-sentinel-config
```

---

## Database Scaling

### DuckDB Read Replicas

```python
"""
DuckDB read replica strategy for analytics queries
Distribute read load across multiple DuckDB instances
"""

class DuckDBReadReplicaPool:
    def __init__(self, replica_count: int = 3):
        self.replicas = []
        self.current_index = 0

        # Create read replicas
        for i in range(replica_count):
            replica_path = f"./data/sec_filings_replica_{i}.duckdb"
            conn = duckdb.connect(replica_path, read_only=True)
            self.replicas.append(conn)

    def get_read_connection(self):
        """Get next replica (round-robin)"""
        conn = self.replicas[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.replicas)
        return conn

    def sync_replicas(self):
        """Sync replicas from master (run periodically)"""
        # Copy master to replicas
        import shutil
        for i in range(len(self.replicas)):
            replica_path = f"./data/sec_filings_replica_{i}.duckdb"
            shutil.copy("./data/sec_filings.duckdb", replica_path)
```

### Supabase Connection Scaling

```python
"""
Supabase connection pool with dynamic sizing
"""

class DynamicSupabasePool:
    def __init__(self, min_size: int = 10, max_size: int = 50):
        self.min_size = min_size
        self.max_size = max_size
        self.current_size = min_size
        self.clients = []

        # Create initial pool
        for _ in range(min_size):
            self.clients.append(self._create_client())

    def scale_up(self, count: int = 5):
        """Add more connections to pool"""
        if self.current_size + count <= self.max_size:
            for _ in range(count):
                self.clients.append(self._create_client())
            self.current_size += count
            logger.info(f"Scaled Supabase pool UP to {self.current_size}")

    def scale_down(self, count: int = 2):
        """Remove connections from pool"""
        if self.current_size - count >= self.min_size:
            for _ in range(count):
                self.clients.pop()
            self.current_size -= count
            logger.info(f"Scaled Supabase pool DOWN to {self.current_size}")

    def auto_scale(self):
        """Auto-scale based on utilization"""
        active_connections = len([c for c in self.clients if c.is_active()])
        utilization = active_connections / self.current_size

        if utilization > 0.8:  # 80% utilization
            self.scale_up()
        elif utilization < 0.3:  # 30% utilization
            self.scale_down()
```

---

## Predictive Scaling

### Time-Based Scaling

```python
"""
Scale up during known high-traffic periods
Scale down during low-traffic periods
"""

SCALING_SCHEDULE = {
    # Market hours (9 AM - 4 PM ET): High volume
    "market_hours": {
        "start_hour": 9,
        "end_hour": 16,
        "timezone": "America/New_York",
        "target_workers": 15,
        "target_redis_memory": "6gb"
    },

    # After-hours (4 PM - 9 AM): Lower volume
    "after_hours": {
        "start_hour": 16,
        "end_hour": 9,
        "timezone": "America/New_York",
        "target_workers": 6,
        "target_redis_memory": "4gb"
    },

    # Weekends: Minimal volume
    "weekends": {
        "days": [5, 6],  # Saturday, Sunday
        "target_workers": 4,
        "target_redis_memory": "2gb"
    }
}


def apply_scheduled_scaling():
    """Apply time-based scaling adjustments"""
    from datetime import datetime
    import pytz

    now = datetime.now(pytz.timezone("America/New_York"))
    current_hour = now.hour
    current_day = now.weekday()

    # Weekend scaling
    if current_day in SCALING_SCHEDULE["weekends"]["days"]:
        target = SCALING_SCHEDULE["weekends"]
        scale_to_target(target)
        return

    # Market hours vs after-hours
    if 9 <= current_hour < 16:
        target = SCALING_SCHEDULE["market_hours"]
    else:
        target = SCALING_SCHEDULE["after_hours"]

    scale_to_target(target)
```

### ML-Based Predictive Scaling

```python
"""
Use historical data to predict load and scale proactively
"""

class PredictiveScaler:
    def __init__(self):
        self.model = self._load_model()
        self.history = []

    def predict_load(self, lookhead_minutes: int = 30) -> Dict[str, float]:
        """Predict load for next N minutes"""
        from datetime import datetime, timedelta

        # Get current metrics
        current_metrics = {
            "hour": datetime.now().hour,
            "day_of_week": datetime.now().weekday(),
            "queue_depth": get_queue_depth(),
            "active_workers": get_active_workers(),
            "recent_throughput": get_recent_throughput()
        }

        # Predict future load
        prediction = self.model.predict([current_metrics])

        return {
            "predicted_queue_depth": prediction[0],
            "predicted_throughput": prediction[1],
            "recommended_workers": prediction[2]
        }

    def proactive_scale(self):
        """Scale based on prediction"""
        prediction = self.predict_load(lookhead_minutes=30)

        recommended = prediction["recommended_workers"]
        current = get_active_workers()

        if recommended > current * 1.5:  # Need 50% more workers
            scale_workers_to(int(recommended))
            logger.info(f"Proactive scale UP to {recommended} workers")
        elif recommended < current * 0.5:  # Can reduce by 50%
            scale_workers_to(int(recommended))
            logger.info(f"Proactive scale DOWN to {recommended} workers")
```

---

## Cost-Aware Scaling

### Budget Constraints

```python
"""
Scale within budget constraints
Prioritize throughput vs cost based on settings
"""

class CostAwareScaler:
    def __init__(self, daily_budget: float = 50.0):
        self.daily_budget = daily_budget
        self.current_spend = 0.0

        # Cost per resource per hour
        self.costs = {
            "celery_worker": 0.05,  # $0.05/hour
            "redis_gb": 0.02,  # $0.02/GB/hour
            "model_call_haiku": 0.00025,  # Per 1K tokens
            "model_call_sonnet": 0.003,
            "supabase_api": 0.00001  # Per request
        }

    def can_scale_up(self, resource: str, count: int) -> bool:
        """Check if we can afford to scale up"""
        hourly_cost = self.costs[resource] * count
        daily_cost = hourly_cost * 24

        projected_spend = self.current_spend + daily_cost
        return projected_spend <= self.daily_budget

    def optimal_scale(self, target_throughput: int) -> Dict[str, int]:
        """
        Calculate optimal scaling configuration
        to meet throughput target within budget
        """
        # Optimize allocation: minimize cost, maximize throughput
        # Subject to: cost <= budget, throughput >= target

        # Simplified: prioritize cheap resources first
        config = {
            "celery_workers": 4,  # Minimum
            "redis_memory_gb": 4
        }

        remaining_budget = self.daily_budget - self.current_spend

        # Add workers until budget exhausted or throughput met
        while remaining_budget > self.costs["celery_worker"] * 24:
            if self._estimate_throughput(config) >= target_throughput:
                break
            config["celery_workers"] += 1
            remaining_budget -= self.costs["celery_worker"] * 24

        return config
```

---

## Monitoring & Alerts for Scaling

### Scaling Metrics

```python
# Prometheus metrics for scaling decisions
from prometheus_client import Gauge

scaling_events = Counter(
    'scaling_events_total',
    'Count of scaling events',
    ['direction', 'reason']
)

current_capacity = Gauge(
    'system_capacity_filings_per_hour',
    'Current system capacity'
)

target_capacity = Gauge(
    'system_target_capacity_filings_per_hour',
    'Target system capacity'
)

scaling_cost = Gauge(
    'scaling_cost_dollars_per_hour',
    'Current cost per hour of scaled resources'
)


def track_scaling_event(direction: str, reason: str, new_replicas: int):
    """Track scaling event"""
    scaling_events.labels(direction=direction, reason=reason).inc()

    # Estimate new capacity
    capacity = estimate_capacity(new_replicas)
    current_capacity.set(capacity)

    # Calculate cost
    cost = calculate_cost(new_replicas)
    scaling_cost.set(cost)
```

### Scaling Alerts

```yaml
# Alert if we're not meeting throughput targets
- alert: ThroughputBelowTarget
  expr: system_capacity_filings_per_hour < system_target_capacity_filings_per_hour
  for: 10m
  annotations:
    summary: "Throughput below target for 10 minutes"
    action: "Consider scaling up workers"

# Alert if we're over-provisioned
- alert: OverProvisionedWorkers
  expr: celery_active_workers > celery_queue_depth / 5
  for: 30m
  annotations:
    summary: "Workers under-utilized for 30 minutes"
    action: "Consider scaling down workers"

# Alert if scaling is happening too frequently
- alert: FrequentScaling
  expr: rate(scaling_events_total[1h]) > 10
  for: 1h
  annotations:
    summary: "Too many scaling events (>10/hour)"
    action: "Review scaling thresholds"
```

---

## Testing Scaling Strategy

### Load Test Script

```bash
#!/bin/bash
# Load test: Simulate 200 filings/hour

for i in {1..200}; do
    # Submit filing processing task
    curl -X POST http://api/process_filing \
        -H "Content-Type: application/json" \
        -d "{\"cik\": \"000${i}\", \"form_type\": \"10-K\"}"

    # Stagger requests (18 seconds apart = 200/hour)
    sleep 18
done
```

### Scaling Test Scenarios

1. **Gradual Load Increase**:
   - Start: 20 filings/hour
   - Increase: +20 filings/hour every 10 minutes
   - Target: 200 filings/hour
   - Expected: Smooth scaling up, no dropped tasks

2. **Sudden Spike**:
   - Start: 30 filings/hour
   - Spike: 150 filings submitted in 1 minute
   - Expected: Rapid scale-up, queue handled within 15 minutes

3. **Load Drop**:
   - Start: 150 filings/hour
   - Drop: 20 filings/hour
   - Expected: Gradual scale-down after 10-minute stabilization

---

## Disaster Recovery

### Failure Scenarios

**Scenario 1: Celery Worker Crash**
- Detection: Worker stops reporting heartbeat
- Response: K8s restarts pod, HPA may scale up temporarily
- Recovery Time: <2 minutes

**Scenario 2: Redis Failure**
- Detection: Redis Sentinel detects master down
- Response: Automatic failover to replica
- Recovery Time: <30 seconds
- Impact: Brief cache miss rate increase

**Scenario 3: Database Overload**
- Detection: Query latency > 1 second for 5 minutes
- Response: Scale up connection pool, add read replicas
- Recovery Time: <5 minutes
- Impact: Increased task latency

---

## Best Practices

1. **Scale Gradually**: Avoid sudden large scaling changes
2. **Use Stabilization Windows**: Wait 5-10 minutes before scaling down
3. **Monitor Cost**: Track spending, set budget alerts
4. **Test Scaling**: Regular load tests to validate scaling behavior
5. **Pre-scale for Known Events**: Use scheduled scaling for predictable load
6. **Reserve Capacity**: Always maintain 20% headroom
7. **Document Incidents**: Track scaling issues and root causes

---

## Next Steps

1. Deploy HPA configurations to Kubernetes
2. Set up scaling metrics in Prometheus
3. Configure Grafana scaling dashboards
4. Run load tests to validate scaling
5. Monitor for 1 week and tune thresholds

---

**Document Version**: 1.0
**Last Updated**: 2025-10-18
**Next Review**: After load testing
