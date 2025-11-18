"""
Comprehensive Health Check System
Monitors database, Redis, external APIs, and system resources
"""

from fastapi import APIRouter, status, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Optional
from datetime import datetime
import asyncio
import httpx
import psutil
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ...data.database_connectors import get_async_session
from ...api.cache import get_redis_client

router = APIRouter()


class ServiceHealth(BaseModel):
    """Health status for a service"""
    status: str = Field(..., description="healthy, degraded, or unhealthy")
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")
    error: Optional[str] = Field(None, description="Error message if unhealthy")
    metadata: Optional[Dict] = Field(default_factory=dict, description="Additional metadata")


class HealthCheckResponse(BaseModel):
    """Complete health check response"""
    status: str = Field(..., description="Overall system status")
    timestamp: str = Field(..., description="Health check timestamp")
    version: str = Field(default="1.0.0", description="Application version")
    services: Dict[str, ServiceHealth] = Field(..., description="Individual service health")
    system: Dict[str, float] = Field(..., description="System resource metrics")


async def check_database(db: AsyncSession) -> ServiceHealth:
    """Check PostgreSQL database health"""
    start_time = datetime.now()
    try:
        # Test connection with simple query
        result = await db.execute(text("SELECT 1"))
        result.scalar()

        # Check connection pool status
        pool = db.get_bind().pool
        pool_size = pool.size()
        checked_out = pool.checkedout()

        response_time = (datetime.now() - start_time).total_seconds() * 1000

        return ServiceHealth(
            status="healthy",
            response_time_ms=response_time,
            metadata={
                "pool_size": pool_size,
                "connections_in_use": checked_out,
                "connections_available": pool_size - checked_out
            }
        )
    except Exception as e:
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        return ServiceHealth(
            status="unhealthy",
            response_time_ms=response_time,
            error=str(e)
        )


async def check_redis(redis_client) -> ServiceHealth:
    """Check Redis cache health"""
    start_time = datetime.now()
    try:
        if redis_client is None:
            return ServiceHealth(
                status="unhealthy",
                error="Redis client not configured"
            )

        # Test connection with PING
        await redis_client.ping()

        # Get Redis info
        info = await redis_client.info()

        response_time = (datetime.now() - start_time).total_seconds() * 1000

        return ServiceHealth(
            status="healthy",
            response_time_ms=response_time,
            metadata={
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "N/A"),
                "uptime_days": info.get("uptime_in_days", 0),
                "evicted_keys": info.get("evicted_keys", 0)
            }
        )
    except Exception as e:
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        return ServiceHealth(
            status="unhealthy",
            response_time_ms=response_time,
            error=str(e)
        )


async def check_sec_edgar() -> ServiceHealth:
    """Check SEC EDGAR API accessibility"""
    start_time = datetime.now()
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://www.sec.gov/cgi-bin/browse-edgar",
                headers={"User-Agent": "SEC Latent Analysis service@example.com"}
            )
            response.raise_for_status()

            response_time = (datetime.now() - start_time).total_seconds() * 1000

            return ServiceHealth(
                status="healthy",
                response_time_ms=response_time,
                metadata={
                    "status_code": response.status_code,
                    "rate_limit_remaining": response.headers.get("X-RateLimit-Remaining", "N/A")
                }
            )
    except Exception as e:
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        return ServiceHealth(
            status="unhealthy",
            response_time_ms=response_time,
            error=str(e)
        )


async def check_celery_workers(redis_client) -> ServiceHealth:
    """Check Celery worker availability"""
    start_time = datetime.now()
    try:
        if redis_client is None:
            return ServiceHealth(
                status="unhealthy",
                error="Redis client not configured"
            )

        # Check for active workers in Celery
        # This is a simplified check - in production, use Celery's inspect API
        active_workers = await redis_client.scard("celery_workers")

        response_time = (datetime.now() - start_time).total_seconds() * 1000

        status = "healthy" if active_workers > 0 else "degraded"

        return ServiceHealth(
            status=status,
            response_time_ms=response_time,
            metadata={
                "active_workers": active_workers,
                "warning": "No active workers" if active_workers == 0 else None
            }
        )
    except Exception as e:
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        return ServiceHealth(
            status="unhealthy",
            response_time_ms=response_time,
            error=str(e)
        )


def get_system_metrics() -> Dict[str, float]:
    """Get system resource metrics"""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    return {
        "cpu_percent": round(cpu_percent, 2),
        "memory_percent": round(memory.percent, 2),
        "memory_available_gb": round(memory.available / (1024**3), 2),
        "disk_percent": round(disk.percent, 2),
        "disk_free_gb": round(disk.free / (1024**3), 2)
    }


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    tags=["health"]
)
async def health_check(
    db: AsyncSession = Depends(get_async_session),
    redis_client = Depends(get_redis_client)
) -> HealthCheckResponse:
    """
    Comprehensive health check endpoint

    Checks:
    - PostgreSQL database connectivity and pool status
    - Redis cache connectivity and memory usage
    - SEC EDGAR API accessibility
    - Celery worker availability
    - System resource utilization

    Returns 200 if all critical services are healthy
    Returns 503 if any critical service is unhealthy
    """
    # Run all health checks concurrently
    db_health, redis_health, sec_health, celery_health = await asyncio.gather(
        check_database(db),
        check_redis(redis_client),
        check_sec_edgar(),
        check_celery_workers(redis_client),
        return_exceptions=True
    )

    # Handle exceptions from gather
    if isinstance(db_health, Exception):
        db_health = ServiceHealth(status="unhealthy", error=str(db_health))
    if isinstance(redis_health, Exception):
        redis_health = ServiceHealth(status="unhealthy", error=str(redis_health))
    if isinstance(sec_health, Exception):
        sec_health = ServiceHealth(status="unhealthy", error=str(sec_health))
    if isinstance(celery_health, Exception):
        celery_health = ServiceHealth(status="unhealthy", error=str(celery_health))

    # Get system metrics
    system_metrics = get_system_metrics()

    # Determine overall status
    services = {
        "database": db_health,
        "redis": redis_health,
        "sec_edgar": sec_health,
        "celery_workers": celery_health
    }

    # Critical services: database, redis
    critical_services = ["database", "redis"]
    critical_healthy = all(
        services[svc].status == "healthy"
        for svc in critical_services
    )

    # Overall status logic
    if not critical_healthy:
        overall_status = "unhealthy"
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif any(svc.status == "unhealthy" for svc in services.values()):
        overall_status = "degraded"
        status_code = status.HTTP_200_OK
    else:
        overall_status = "healthy"
        status_code = status.HTTP_200_OK

    response = HealthCheckResponse(
        status=overall_status,
        timestamp=datetime.utcnow().isoformat(),
        services=services,
        system=system_metrics
    )

    return JSONResponse(
        status_code=status_code,
        content=response.dict()
    )


@router.get(
    "/health/liveness",
    status_code=status.HTTP_200_OK,
    tags=["health"]
)
async def liveness_probe():
    """
    Kubernetes liveness probe
    Returns 200 if application is running
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get(
    "/health/readiness",
    status_code=status.HTTP_200_OK,
    tags=["health"]
)
async def readiness_probe(
    db: AsyncSession = Depends(get_async_session),
    redis_client = Depends(get_redis_client)
):
    """
    Kubernetes readiness probe
    Returns 200 only if application is ready to serve traffic
    """
    # Check critical services
    db_health, redis_health = await asyncio.gather(
        check_database(db),
        check_redis(redis_client),
        return_exceptions=True
    )

    if isinstance(db_health, Exception):
        db_health = ServiceHealth(status="unhealthy", error=str(db_health))
    if isinstance(redis_health, Exception):
        redis_health = ServiceHealth(status="unhealthy", error=str(redis_health))

    is_ready = (
        db_health.status == "healthy" and
        redis_health.status == "healthy"
    )

    if not is_ready:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not ready",
                "timestamp": datetime.utcnow().isoformat(),
                "database": db_health.status,
                "redis": redis_health.status
            }
        )

    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat()
    }
