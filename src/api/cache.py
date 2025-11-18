"""
Redis Caching Layer
Handles response caching, connection pooling, and compression
"""

import json
import hashlib
import gzip
from typing import Optional, Any, Dict
from datetime import timedelta
import redis.asyncio as redis
import logging

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages Redis caching with compression and serialization"""

    def __init__(self, redis_client: redis.Redis, default_ttl: int = 3600):
        self.redis = redis_client
        self.default_ttl = default_ttl
        self.compression_threshold = 1024  # Compress if data > 1KB

    def _generate_key(self, prefix: str, params: Dict[str, Any]) -> str:
        """Generate cache key from prefix and parameters"""
        # Sort parameters for consistent keys
        sorted_params = json.dumps(params, sort_keys=True)
        param_hash = hashlib.md5(sorted_params.encode()).hexdigest()
        return f"{prefix}:{param_hash}"

    def _compress(self, data: bytes) -> bytes:
        """Compress data if above threshold"""
        if len(data) > self.compression_threshold:
            return gzip.compress(data)
        return data

    def _decompress(self, data: bytes) -> bytes:
        """Decompress data if needed"""
        try:
            return gzip.decompress(data)
        except gzip.BadGzipFile:
            # Not compressed
            return data

    async def get(self, prefix: str, params: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """Retrieve cached value"""
        if not self.redis:
            return None

        try:
            params = params or {}
            cache_key = self._generate_key(prefix, params)

            cached = await self.redis.get(cache_key)
            if cached:
                # Decompress and deserialize
                decompressed = self._decompress(cached.encode() if isinstance(cached, str) else cached)
                data = json.loads(decompressed)
                logger.debug(f"Cache hit: {cache_key}")
                return data

            logger.debug(f"Cache miss: {cache_key}")
            return None

        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    async def set(
        self,
        prefix: str,
        value: Any,
        params: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None
    ) -> bool:
        """Store value in cache"""
        if not self.redis:
            return False

        try:
            params = params or {}
            cache_key = self._generate_key(prefix, params)
            ttl = ttl or self.default_ttl

            # Serialize and compress
            serialized = json.dumps(value).encode()
            compressed = self._compress(serialized)

            # Store with TTL
            await self.redis.setex(
                cache_key,
                timedelta(seconds=ttl),
                compressed
            )

            logger.debug(f"Cache set: {cache_key} (TTL: {ttl}s)")
            return True

        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    async def delete(self, prefix: str, params: Optional[Dict[str, Any]] = None) -> bool:
        """Delete cached value"""
        if not self.redis:
            return False

        try:
            params = params or {}
            cache_key = self._generate_key(prefix, params)
            await self.redis.delete(cache_key)
            logger.debug(f"Cache delete: {cache_key}")
            return True

        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        if not self.redis:
            return 0

        try:
            keys = await self.redis.keys(pattern)
            if keys:
                deleted = await self.redis.delete(*keys)
                logger.info(f"Cleared {deleted} cache keys matching: {pattern}")
                return deleted
            return 0

        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return 0

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.redis:
            return {"status": "not configured"}

        try:
            info = await self.redis.info("stats")
            return {
                "status": "connected",
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "total_keys": await self.redis.dbsize()
            }

        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"status": "error", "error": str(e)}


class CacheKey:
    """Cache key prefixes for different data types"""
    FILING_METADATA = "filing:metadata"
    FILING_TEXT = "filing:text"
    FILING_ANALYSIS = "filing:analysis"
    PREDICTION = "prediction"
    SIGNAL = "signal"
    VALIDATION = "validation"
    MARKET_DATA = "market:data"
    COMPANY_INFO = "company:info"
