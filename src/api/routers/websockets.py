"""
WebSockets Router
Real-time streaming endpoints for filings, predictions, and signals
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/filings")
async def websocket_filings(websocket: WebSocket):
    """
    WebSocket endpoint for real-time filing updates

    Streams:
    - New filing notifications
    - Filing analysis completion
    - Updated metadata
    """
    manager = websocket.app.state.ws_manager

    if not await manager.connect(websocket, "filings"):
        await websocket.close(code=1008, reason="Connection limit reached")
        return

    try:
        # Send welcome message
        await manager.send_personal(
            {
                "type": "connection_established",
                "channel": "filings",
                "timestamp": datetime.utcnow().isoformat()
            },
            websocket
        )

        # Keep connection alive and handle messages
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            # Handle client messages
            if message.get("type") == "ping":
                await manager.send_personal(
                    {"type": "pong", "timestamp": datetime.utcnow().isoformat()},
                    websocket
                )
            elif message.get("type") == "subscribe":
                # Handle subscription filters
                logger.info(f"Client subscribed with filters: {message.get('filters')}")

    except WebSocketDisconnect:
        manager.disconnect(websocket, "filings")
        logger.info("WebSocket disconnected: filings")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        manager.disconnect(websocket, "filings")


@router.websocket("/predictions")
async def websocket_predictions(websocket: WebSocket):
    """
    WebSocket endpoint for real-time prediction updates

    Streams:
    - New predictions
    - Prediction confidence updates
    - Model version changes
    """
    manager = websocket.app.state.ws_manager

    if not await manager.connect(websocket, "predictions"):
        await websocket.close(code=1008, reason="Connection limit reached")
        return

    try:
        await manager.send_personal(
            {
                "type": "connection_established",
                "channel": "predictions",
                "timestamp": datetime.utcnow().isoformat()
            },
            websocket
        )

        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "ping":
                await manager.send_personal(
                    {"type": "pong", "timestamp": datetime.utcnow().isoformat()},
                    websocket
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket, "predictions")
        logger.info("WebSocket disconnected: predictions")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        manager.disconnect(websocket, "predictions")


@router.websocket("/signals")
async def websocket_signals(websocket: WebSocket):
    """
    WebSocket endpoint for real-time trading signal updates

    Streams:
    - New signals
    - Signal strength updates
    - Signal expiration notifications
    """
    manager = websocket.app.state.ws_manager

    if not await manager.connect(websocket, "signals"):
        await websocket.close(code=1008, reason="Connection limit reached")
        return

    try:
        await manager.send_personal(
            {
                "type": "connection_established",
                "channel": "signals",
                "timestamp": datetime.utcnow().isoformat()
            },
            websocket
        )

        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "ping":
                await manager.send_personal(
                    {"type": "pong", "timestamp": datetime.utcnow().isoformat()},
                    websocket
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket, "signals")
        logger.info("WebSocket disconnected: signals")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        manager.disconnect(websocket, "signals")


@router.websocket("/market")
async def websocket_market_data(
    websocket: WebSocket,
    symbols: Optional[str] = Query(None, description="Comma-separated ticker symbols")
):
    """
    WebSocket endpoint for real-time market data

    Streams:
    - Price updates
    - Volume data
    - Market events
    """
    manager = websocket.app.state.ws_manager

    if not await manager.connect(websocket, "market_data"):
        await websocket.close(code=1008, reason="Connection limit reached")
        return

    try:
        symbol_list = symbols.split(",") if symbols else []

        await manager.send_personal(
            {
                "type": "connection_established",
                "channel": "market_data",
                "subscribed_symbols": symbol_list,
                "timestamp": datetime.utcnow().isoformat()
            },
            websocket
        )

        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "ping":
                await manager.send_personal(
                    {"type": "pong", "timestamp": datetime.utcnow().isoformat()},
                    websocket
                )
            elif message.get("type") == "subscribe_symbols":
                # Update subscribed symbols
                new_symbols = message.get("symbols", [])
                logger.info(f"Updated symbol subscription: {new_symbols}")

    except WebSocketDisconnect:
        manager.disconnect(websocket, "market_data")
        logger.info("WebSocket disconnected: market_data")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        manager.disconnect(websocket, "market_data")
