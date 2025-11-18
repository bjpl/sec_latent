"""
Rate Limiting Middleware
DDoS prevention and request throttling
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional, Dict
from datetime import datetime, timedelta
import logging
from collections import defaultdict
import asyncio

from ..security.audit import AuditLogger, AuditEventType

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter implementation
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_size: Optional[int] = None
    ):
        """
        Initialize RateLimiter

        Args:
            requests_per_minute: Maximum requests per minute
            burst_size: Maximum burst size (default: 2x rate)
        """
        self.rate = requests_per_minute / 60.0  # Requests per second
        self.burst_size = burst_size or (requests_per_minute * 2)

        # Storage: {identifier: (tokens, last_update)}
        self._buckets: Dict[str, tuple[float, datetime]] = {}
        self._lock = asyncio.Lock()

    async def is_allowed(self, identifier: str) -> tuple[bool, dict]:
        """
        Check if request is allowed under rate limit

        Args:
            identifier: Unique identifier (user_id, IP, API key)

        Returns:
            Tuple of (allowed, info_dict)
        """
        async with self._lock:
            now = datetime.utcnow()

            # Get or initialize bucket
            if identifier not in self._buckets:
                self._buckets[identifier] = (self.burst_size, now)

            tokens, last_update = self._buckets[identifier]

            # Calculate time elapsed and new tokens
            elapsed = (now - last_update).total_seconds()
            new_tokens = elapsed * self.rate
            tokens = min(self.burst_size, tokens + new_tokens)

            # Check if request can be served
            if tokens >= 1.0:
                tokens -= 1.0
                self._buckets[identifier] = (tokens, now)
                return True, {
                    "remaining": int(tokens),
                    "limit": int(self.burst_size),
                    "reset": (now + timedelta(seconds=60/self.rate)).isoformat()
                }
            else:
                # Rate limit exceeded
                return False, {
                    "remaining": 0,
                    "limit": int(self.burst_size),
                    "reset": (now + timedelta(seconds=(1.0 - tokens) / self.rate)).isoformat(),
                    "retry_after": int((1.0 - tokens) / self.rate)
                }

    def reset(self, identifier: str):
        """Reset rate limit for identifier"""
        if identifier in self._buckets:
            del self._buckets[identifier]

    def cleanup_old_buckets(self, max_age_minutes: int = 60):
        """
        Clean up old buckets to prevent memory bloat

        Args:
            max_age_minutes: Maximum age of buckets to keep
        """
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=max_age_minutes)

        to_remove = [
            identifier
            for identifier, (_, last_update) in self._buckets.items()
            if last_update < cutoff
        ]

        for identifier in to_remove:
            del self._buckets[identifier]

        if to_remove:
            logger.debug(f"Cleaned up {len(to_remove)} old rate limit buckets")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware for rate limiting requests
    """

    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        burst_size: Optional[int] = None,
        audit_logger: Optional[AuditLogger] = None,
        excluded_paths: list[str] = None,
        custom_limits: Dict[str, int] = None
    ):
        """
        Initialize RateLimitMiddleware

        Args:
            app: FastAPI application
            requests_per_minute: Default requests per minute
            burst_size: Maximum burst size
            audit_logger: Optional AuditLogger
            excluded_paths: Paths to exclude from rate limiting
            custom_limits: Custom rate limits per path
        """
        super().__init__(app)
        self.default_limiter = RateLimiter(requests_per_minute, burst_size)
        self.audit_logger = audit_logger

        # Excluded paths (health checks, etc.)
        self.excluded_paths = excluded_paths or [
            "/health",
            "/docs",
            "/openapi.json"
        ]

        # Custom rate limits per path
        self.custom_limiters = {}
        if custom_limits:
            for path, limit in custom_limits.items():
                self.custom_limiters[path] = RateLimiter(limit, burst_size)

        # Start cleanup task
        self._cleanup_task = None

    async def dispatch(self, request: Request, call_next):
        """
        Process request through rate limiting

        Args:
            request: FastAPI request
            call_next: Next middleware in chain

        Returns:
            Response from next middleware
        """
        # Skip rate limiting for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        # Determine identifier (user_id > api_key > IP)
        identifier = None
        if hasattr(request.state, 'user_id'):
            identifier = request.state.user_id
        elif hasattr(request.state, 'api_key_id'):
            identifier = f"api_key:{request.state.api_key_id}"
        elif request.client:
            identifier = request.client.host
        else:
            identifier = "anonymous"

        # Get appropriate rate limiter
        limiter = self.default_limiter
        for path, custom_limiter in self.custom_limiters.items():
            if request.url.path.startswith(path):
                limiter = custom_limiter
                break

        # Check rate limit
        allowed, info = await limiter.is_allowed(identifier)

        if not allowed:
            # Log rate limit violation
            if self.audit_logger:
                self.audit_logger.log_security_event(
                    event_type=AuditEventType.SECURITY_RATE_LIMIT,
                    message=f"Rate limit exceeded for {identifier}",
                    ip_address=request.client.host if request.client else None,
                    user_id=getattr(request.state, 'user_id', None),
                    details={
                        "path": str(request.url.path),
                        "identifier": identifier,
                        **info
                    }
                )

            logger.warning(f"Rate limit exceeded for {identifier} on {request.url.path}")

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={
                    "X-RateLimit-Limit": str(info["limit"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": info["reset"],
                    "Retry-After": str(info.get("retry_after", 60))
                }
            )

        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
        response.headers["X-RateLimit-Reset"] = info["reset"]

        return response

    async def start_cleanup(self):
        """Start periodic cleanup of old buckets"""
        while True:
            await asyncio.sleep(3600)  # Run every hour
            self.default_limiter.cleanup_old_buckets()
            for limiter in self.custom_limiters.values():
                limiter.cleanup_old_buckets()
