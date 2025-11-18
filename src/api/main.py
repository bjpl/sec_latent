"""
FastAPI Main Application
Handles CORS, WebSocket connections, Redis pooling, and error handling
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import asyncio
import redis.asyncio as redis
from typing import Dict, Set, Optional
import logging
from datetime import datetime
import uvicorn

from .routers import filings, predictions, signals, validation, websockets
from .cache import CacheManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections with support for 2000+ concurrent connections"""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "filings": set(),
            "predictions": set(),
            "signals": set(),
            "market_data": set()
        }
        self.connection_count = 0
        self.max_connections = 2000

    async def connect(self, websocket: WebSocket, channel: str = "filings") -> bool:
        """Accept WebSocket connection if under limit"""
        if self.connection_count >= self.max_connections:
            logger.warning(f"Connection limit reached: {self.connection_count}")
            return False

        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = set()
        self.active_connections[channel].add(websocket)
        self.connection_count += 1
        logger.info(f"WebSocket connected to {channel}. Total: {self.connection_count}")
        return True

    def disconnect(self, websocket: WebSocket, channel: str = "filings"):
        """Remove WebSocket connection"""
        if channel in self.active_connections:
            self.active_connections[channel].discard(websocket)
            self.connection_count = max(0, self.connection_count - 1)
            logger.info(f"WebSocket disconnected from {channel}. Total: {self.connection_count}")

    async def broadcast(self, message: dict, channel: str = "filings"):
        """Broadcast message to all connections in channel"""
        if channel not in self.active_connections:
            return

        disconnected = set()
        for connection in self.active_connections[channel]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
                disconnected.add(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection, channel)

    async def send_personal(self, message: dict, websocket: WebSocket):
        """Send message to specific WebSocket"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending to WebSocket: {e}")
            raise


# Global WebSocket manager
ws_manager = WebSocketManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown"""
    # Startup
    logger.info("Starting SEC Latent Analysis API...")

    # Initialize Redis connection pool
    app.state.redis = redis.Redis(
        host='localhost',
        port=6379,
        db=0,
        decode_responses=True,
        max_connections=50,
        socket_keepalive=True,
        socket_connect_timeout=5,
        retry_on_timeout=True
    )

    # Initialize cache manager
    app.state.cache = CacheManager(app.state.redis)

    # Test Redis connection
    try:
        await app.state.redis.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        logger.warning("Starting without Redis cache")
        app.state.redis = None
        app.state.cache = None

    # Store WebSocket manager
    app.state.ws_manager = ws_manager

    logger.info("API startup complete")

    yield

    # Shutdown
    logger.info("Shutting down API...")

    # Close Redis connection
    if app.state.redis:
        await app.state.redis.close()
        logger.info("Redis connection closed")

    logger.info("API shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="SEC Latent Analysis API",
    description="Advanced SEC filing analysis with latent space predictions",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add GZip compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Error handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "body": exc.body,
            "timestamp": datetime.utcnow().isoformat()
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "timestamp": datetime.utcnow().isoformat()
        },
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    redis_status = "connected"
    if app.state.redis:
        try:
            await app.state.redis.ping()
        except Exception:
            redis_status = "disconnected"
    else:
        redis_status = "not configured"

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "redis": redis_status,
        "websocket_connections": app.state.ws_manager.connection_count
    }


# Include routers
app.include_router(filings.router, prefix="/api/v1/filings", tags=["filings"])
app.include_router(predictions.router, prefix="/api/v1/predictions", tags=["predictions"])
app.include_router(signals.router, prefix="/api/v1/signals", tags=["signals"])
app.include_router(validation.router, prefix="/api/v1/validation", tags=["validation"])
app.include_router(websockets.router, prefix="/ws", tags=["websockets"])


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "SEC Latent Analysis API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
