"""
WebSocket handler for real-time document processing status updates.
Uses Redis pubsub for cross-service communication.
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import asyncio
from shared.logging.logger import get_logger
from shared.database.redis_client import redis_client

logger = get_logger("websocket_handler")


class ConnectionManager:
    """Manages WebSocket connections for document status updates."""
    
    def __init__(self):
        # Map of content_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self._pubsub = None
        self._listener_task = None
    
    async def connect(self, websocket: WebSocket, content_id: str):
        """Accept a new WebSocket connection for a document."""
        await websocket.accept()
        
        if content_id not in self.active_connections:
            self.active_connections[content_id] = set()
        
        self.active_connections[content_id].add(websocket)
        logger.info(f"WebSocket connected for document {content_id}. Active connections: {len(self.active_connections[content_id])}")
        
        # Start Redis listener if not already running
        if not self._listener_task:
            self._listener_task = asyncio.create_task(self._listen_redis())
    
    def disconnect(self, websocket: WebSocket, content_id: str):
        """Remove a WebSocket connection."""
        if content_id in self.active_connections:
            self.active_connections[content_id].discard(websocket)
            
            # Clean up empty sets
            if not self.active_connections[content_id]:
                del self.active_connections[content_id]
        
        logger.info(f"WebSocket disconnected for document {content_id}")
    
    async def send_status(self, content_id: str, status: dict):
        """Send status update to all connections for a document."""
        if content_id not in self.active_connections:
            return
        
        message = json.dumps(status)
        disconnected = set()
        
        for websocket in self.active_connections[content_id]:
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.warning(f"Failed to send to websocket: {e}")
                disconnected.add(websocket)
        
        # Clean up disconnected websockets
        for ws in disconnected:
            self.disconnect(ws, content_id)
    
    async def publish_status(self, content_id: str, status: dict):
        """
        Publish status update to Redis for cross-service communication.
        This allows vectorization service to send updates back.
        """
        try:
            channel = f"document:status:{content_id}"
            message = json.dumps(status)
            await redis_client.client.publish(channel, message)
            logger.info(f"Published status to Redis channel {channel}: {status}")
        except Exception as e:
            logger.error(f"Failed to publish to Redis: {e}")
    
    async def _listen_redis(self):
        """Listen for status updates from Redis pubsub."""
        try:
            pubsub = redis_client.client.pubsub()
            
            # Subscribe to all document status channels
            await pubsub.psubscribe("document:status:*")
            
            logger.info("Started Redis pubsub listener for document status")
            
            async for message in pubsub.listen():
                if message["type"] == "pmessage":
                    try:
                        # Extract content_id from channel name
                        channel = message["channel"].decode()
                        content_id = channel.split(":")[-1]
                        
                        # Parse status update
                        data = message["data"].decode()
                        status = json.loads(data)
                        
                        # Send to all connected WebSockets for this document
                        await self.send_status(content_id, status)
                        
                    except Exception as e:
                        logger.error(f"Error processing Redis message: {e}")
        
        except Exception as e:
            logger.error(f"Redis listener error: {e}")
        finally:
            if pubsub:
                await pubsub.close()


# Global connection manager instance
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, content_id: str):
    """
    WebSocket endpoint for document processing status updates.
    
    Client receives messages in format:
    {
        "status": "uploading" | "processing" | "vectorizing" | "completed" | "failed",
        "progress": 0-100,
        "message": "Processing chunks...",
        "processed_chunks": 10,
        "total_chunks": 45
    }
    """
    await manager.connect(websocket, content_id)
    
    try:
        # Send initial status from database
        from shared.database.mongodb_client import mongodb_client
        db = mongodb_client.get_database()
        doc = await db.content.find_one({"content_id": content_id})
        
        if doc:
            initial_status = {
                "status": doc.get("status", "unknown"),
                "progress": int((doc.get("processed_chunks", 0) / doc.get("total_chunks", 1)) * 100) if doc.get("total_chunks", 0) > 0 else 0,
                "processed_chunks": doc.get("processed_chunks", 0),
                "total_chunks": doc.get("total_chunks", 0),
                "message": f"Status: {doc.get('status', 'unknown')}"
            }
            await websocket.send_text(json.dumps(initial_status))
        
        # Keep connection alive with heartbeats
        while True:
            try:
                # Wait for client messages (heartbeat/ping)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                
                # Client can send {"type": "ping"} to keep connection alive
                if data:
                    message = json.loads(data)
                    if message.get("type") == "ping":
                        await websocket.send_text(json.dumps({"type": "pong"}))
                
            except asyncio.TimeoutError:
                # Send heartbeat to check connection
                await websocket.send_text(json.dumps({"type": "heartbeat"}))
            
    except WebSocketDisconnect:
        logger.info(f"Client disconnected from document {content_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket, content_id)

