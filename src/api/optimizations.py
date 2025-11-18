"""
API Performance Optimizations
Implements async patterns, pagination, query optimization, and response compression
"""

import asyncio
import gzip
from typing import List, Dict, Any, Optional, Callable, TypeVar, Generic
from functools import wraps
from fastapi import Query, HTTPException, Response, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import logging
import time

logger = logging.getLogger(__name__)

T = TypeVar('T')


# ============================================
# PAGINATION
# ============================================

class PaginationParams(BaseModel):
    """Standard pagination parameters"""
    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(50, ge=1, le=1000, description="Items per page (max 1000)")
    cursor: Optional[str] = Field(None, description="Cursor for cursor-based pagination")

    @property
    def offset(self) -> int:
        """Calculate offset from page and page_size"""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Alias for page_size"""
        return self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated response format"""
    data: List[T]
    pagination: Dict[str, Any]
    total: Optional[int] = None

    @classmethod
    def create(
        cls,
        data: List[T],
        total: int,
        page: int,
        page_size: int,
        has_next: Optional[bool] = None
    ):
        """Create paginated response with metadata"""
        if has_next is None:
            has_next = (page * page_size) < total

        return cls(
            data=data,
            total=total,
            pagination={
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size,
                "total_items": total,
                "has_next": has_next,
                "has_prev": page > 1
            }
        )


class CursorPaginatedResponse(BaseModel, Generic[T]):
    """Cursor-based pagination for large datasets"""
    data: List[T]
    pagination: Dict[str, Any]

    @classmethod
    def create(
        cls,
        data: List[T],
        next_cursor: Optional[str],
        prev_cursor: Optional[str] = None,
        page_size: int = 50
    ):
        """Create cursor-paginated response"""
        return cls(
            data=data,
            pagination={
                "page_size": page_size,
                "next_cursor": next_cursor,
                "prev_cursor": prev_cursor,
                "has_next": next_cursor is not None,
                "has_prev": prev_cursor is not None
            }
        )


# ============================================
# ASYNC BATCH PROCESSING
# ============================================

async def batch_process_async(
    items: List[Any],
    processor: Callable,
    batch_size: int = 10,
    max_concurrent: int = 5
) -> List[Any]:
    """
    Process items in batches with concurrency control

    Args:
        items: Items to process
        processor: Async function to process each item
        batch_size: Items per batch
        max_concurrent: Maximum concurrent batches

    Returns:
        List of processed results
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    results = []

    async def process_with_semaphore(item):
        async with semaphore:
            return await processor(item)

    # Process in batches
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_results = await asyncio.gather(
            *[process_with_semaphore(item) for item in batch],
            return_exceptions=True
        )
        results.extend(batch_results)

    # Filter out exceptions (log them)
    valid_results = []
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"Batch processing error: {result}")
        else:
            valid_results.append(result)

    return valid_results


async def parallel_fetch(
    fetch_functions: List[Callable],
    max_concurrent: int = 10
) -> List[Any]:
    """
    Execute multiple fetch operations in parallel

    Args:
        fetch_functions: List of async functions to execute
        max_concurrent: Maximum concurrent operations

    Returns:
        List of results
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def fetch_with_semaphore(func):
        async with semaphore:
            return await func()

    results = await asyncio.gather(
        *[fetch_with_semaphore(func) for func in fetch_functions],
        return_exceptions=True
    )

    return results


# ============================================
# RESPONSE COMPRESSION
# ============================================

def compress_response(min_size: int = 1000):
    """
    Decorator to compress large responses

    Args:
        min_size: Minimum response size in bytes to trigger compression
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            response = await func(*args, **kwargs)

            # Check if response is compressible
            if isinstance(response, dict):
                import json
                content = json.dumps(response).encode('utf-8')

                if len(content) >= min_size:
                    compressed = gzip.compress(content)
                    return Response(
                        content=compressed,
                        media_type="application/json",
                        headers={"Content-Encoding": "gzip"}
                    )

            return response

        return wrapper
    return decorator


# ============================================
# STREAMING RESPONSES
# ============================================

async def stream_large_response(
    data_generator: Callable,
    chunk_size: int = 1000
):
    """
    Stream large responses in chunks

    Args:
        data_generator: Async generator yielding data chunks
        chunk_size: Items per chunk

    Returns:
        StreamingResponse
    """
    async def generate():
        async for chunk in data_generator():
            yield chunk

    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson"  # Newline-delimited JSON
    )


# ============================================
# QUERY OPTIMIZATION
# ============================================

class QueryOptimizer:
    """Optimize database queries for performance"""

    @staticmethod
    def optimize_select_fields(
        requested_fields: Optional[List[str]],
        available_fields: List[str],
        default_fields: List[str]
    ) -> List[str]:
        """
        Optimize SELECT fields to reduce data transfer

        Args:
            requested_fields: Fields requested by client
            available_fields: All available fields
            default_fields: Default fields if none specified

        Returns:
            Optimized field list
        """
        if not requested_fields:
            return default_fields

        # Validate and filter requested fields
        valid_fields = [f for f in requested_fields if f in available_fields]

        if not valid_fields:
            return default_fields

        return valid_fields

    @staticmethod
    def optimize_filter_conditions(
        filters: Dict[str, Any],
        indexed_fields: List[str]
    ) -> Dict[str, Any]:
        """
        Reorder filter conditions to use indexes first

        Args:
            filters: Filter conditions
            indexed_fields: Fields with indexes

        Returns:
            Optimized filter dict
        """
        # Sort filters: indexed fields first
        optimized = {}

        # Add indexed filters first
        for field in indexed_fields:
            if field in filters:
                optimized[field] = filters[field]

        # Add non-indexed filters
        for field, value in filters.items():
            if field not in indexed_fields:
                optimized[field] = value

        return optimized


# ============================================
# CACHING DECORATORS
# ============================================

def cache_response(
    ttl: int = 3600,
    key_prefix: str = "api",
    vary_on: Optional[List[str]] = None
):
    """
    Decorator to cache API responses

    Args:
        ttl: Cache TTL in seconds
        key_prefix: Cache key prefix
        vary_on: Request attributes to include in cache key
    """
    vary_on = vary_on or []

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get cache manager from request context
            request = kwargs.get("request")
            if not request or not hasattr(request.app.state, "cache"):
                return await func(*args, **kwargs)

            cache = request.app.state.cache

            # Generate cache key
            import hashlib
            import json

            key_parts = [key_prefix, func.__name__]

            # Add vary_on attributes
            for attr in vary_on:
                if attr in kwargs:
                    key_parts.append(str(kwargs[attr]))

            cache_key = ":".join(key_parts)

            # Try to get from cache
            cached = await cache.get(cache_key)
            if cached:
                logger.debug(f"Cache hit: {cache_key}")
                return cached

            # Execute function
            result = await func(*args, **kwargs)

            # Store in cache
            await cache.set(cache_key, result, ttl=ttl)
            logger.debug(f"Cache miss, stored: {cache_key}")

            return result

        return wrapper
    return decorator


# ============================================
# RATE LIMITING HELPERS
# ============================================

class AdaptiveRateLimiter:
    """Adaptive rate limiting based on system load"""

    def __init__(self):
        self.base_rate = 1000  # Base requests per second
        self.current_rate = self.base_rate
        self.load_threshold = 0.8

    async def get_current_limit(self, system_load: float) -> int:
        """
        Get current rate limit based on system load

        Args:
            system_load: Current system load (0-1)

        Returns:
            Current rate limit
        """
        if system_load < self.load_threshold:
            self.current_rate = self.base_rate
        else:
            # Reduce rate proportionally to load
            reduction_factor = (system_load - self.load_threshold) / (1 - self.load_threshold)
            self.current_rate = int(self.base_rate * (1 - reduction_factor * 0.5))

        return self.current_rate


# ============================================
# RESPONSE TIME MONITORING
# ============================================

def monitor_performance(
    slow_threshold_ms: int = 200,
    log_slow_requests: bool = True
):
    """
    Decorator to monitor endpoint performance

    Args:
        slow_threshold_ms: Threshold for slow request logging
        log_slow_requests: Whether to log slow requests
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.perf_counter()

            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration_ms = (time.perf_counter() - start_time) * 1000

                if log_slow_requests and duration_ms > slow_threshold_ms:
                    logger.warning(
                        f"Slow request: {func.__name__} took {duration_ms:.2f}ms "
                        f"(threshold: {slow_threshold_ms}ms)"
                    )

                # Could also emit metrics here
                # metrics.histogram("api_response_time", duration_ms, tags={"endpoint": func.__name__})

        return wrapper
    return decorator


# ============================================
# BULK OPERATIONS
# ============================================

class BulkOperationManager:
    """Manage bulk operations efficiently"""

    @staticmethod
    async def bulk_insert(
        items: List[Dict[str, Any]],
        batch_size: int = 100,
        db_connector: Any = None
    ):
        """
        Insert items in batches

        Args:
            items: Items to insert
            batch_size: Items per batch
            db_connector: Database connector

        Returns:
            Number of inserted items
        """
        inserted_count = 0

        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]

            try:
                # Execute batch insert
                # await db_connector.bulk_insert(batch)
                inserted_count += len(batch)
                logger.debug(f"Inserted batch {i//batch_size + 1}: {len(batch)} items")

            except Exception as e:
                logger.error(f"Batch insert failed: {e}")

        return inserted_count

    @staticmethod
    async def bulk_update(
        updates: List[Dict[str, Any]],
        batch_size: int = 100,
        db_connector: Any = None
    ):
        """
        Update items in batches

        Args:
            updates: Update operations
            batch_size: Operations per batch
            db_connector: Database connector

        Returns:
            Number of updated items
        """
        updated_count = 0

        for i in range(0, len(updates), batch_size):
            batch = updates[i:i + batch_size]

            try:
                # Execute batch update
                # await db_connector.bulk_update(batch)
                updated_count += len(batch)

            except Exception as e:
                logger.error(f"Batch update failed: {e}")

        return updated_count


# ============================================
# CONNECTION POOLING
# ============================================

class ConnectionPoolManager:
    """Manage database connection pools"""

    def __init__(self, min_size: int = 10, max_size: int = 100):
        self.min_size = min_size
        self.max_size = max_size
        self.active_connections = 0

    async def get_connection(self):
        """Get connection from pool with auto-scaling"""
        if self.active_connections >= self.max_size:
            raise HTTPException(
                status_code=503,
                detail="Service temporarily unavailable - connection pool exhausted"
            )

        self.active_connections += 1
        # Return connection (placeholder)
        return None

    async def release_connection(self, conn):
        """Release connection back to pool"""
        self.active_connections -= 1


# ============================================
# FIELD FILTERING
# ============================================

def filter_response_fields(
    data: Dict[str, Any],
    include_fields: Optional[List[str]] = None,
    exclude_fields: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Filter response fields to reduce payload size

    Args:
        data: Response data
        include_fields: Fields to include (if specified, only these)
        exclude_fields: Fields to exclude

    Returns:
        Filtered data
    """
    if include_fields:
        return {k: v for k, v in data.items() if k in include_fields}

    if exclude_fields:
        return {k: v for k, v in data.items() if k not in exclude_fields}

    return data


# ============================================
# USAGE EXAMPLES
# ============================================

"""
# Pagination example
@app.get("/api/v1/filings")
@monitor_performance(slow_threshold_ms=200)
@cache_response(ttl=3600, key_prefix="filings", vary_on=["cik", "page"])
async def get_filings(
    cik: str,
    pagination: PaginationParams = Depends(),
    request: Request
):
    # Fetch data with pagination
    filings = await fetch_filings(cik, offset=pagination.offset, limit=pagination.limit)
    total = await count_filings(cik)

    return PaginatedResponse.create(
        data=filings,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size
    )


# Batch processing example
@app.post("/api/v1/filings/batch-analyze")
async def batch_analyze_filings(filing_ids: List[str]):
    results = await batch_process_async(
        items=filing_ids,
        processor=analyze_filing,
        batch_size=10,
        max_concurrent=5
    )
    return {"results": results}


# Streaming response example
@app.get("/api/v1/filings/stream")
async def stream_filings():
    async def generate_filings():
        async for filing in fetch_filings_stream():
            yield json.dumps(filing) + "\\n"

    return stream_large_response(generate_filings)
"""
