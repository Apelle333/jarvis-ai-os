"""
JARVIS AI Operating System - WebSocket API
Handles real-time communication with the AI system
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from typing import Dict, Optional
import json
import logging
import asyncio
from datetime import datetime

from agents.main_agent import MainAgent
from api.dependencies import get_brain, get_main_agent

logger = logging.getLogger(__name__)

router = APIRouter()

# Connection manager for WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_info: Dict[str, dict] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.connection_info[client_id] = {
            "connected_at": datetime.now(),
            "last_activity": datetime.now(),
            "message_count": 0
        }
        logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.connection_info:
            del self.connection_info[client_id]
        logger.info(f"Client {client_id} disconnected. Remaining connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(json.dumps(message))
                self.connection_info[client_id]["last_activity"] = datetime.now()
                self.connection_info[client_id]["message_count"] += 1
            except Exception as e:
                logger.error(f"Error sending message to client {client_id}: {e}")
                self.disconnect(client_id)

    async def broadcast(self, message: dict):
        disconnected = []
        for client_id, connection in self.active_connections.items():
            try:
                await connection.send_text(json.dumps(message))
                self.connection_info[client_id]["last_activity"] = datetime.now()
                self.connection_info[client_id]["message_count"] += 1
            except Exception as e:
                logger.error(f"Error broadcasting to client {client_id}: {e}")
                disconnected.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected:
            self.disconnect(client_id)

    def get_connection_count(self) -> int:
        return len(self.active_connections)

    def get_connection_info(self) -> dict:
        return self.connection_info.copy()


manager = ConnectionManager()


@router.websocket("/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str, agent: MainAgent = Depends(get_main_agent)):
    """
    WebSocket endpoint for real-time communication
    """
    await manager.connect(websocket, client_id)

    try:
        # Send welcome message
        await manager.send_personal_message({
            "type": "connection",
            "status": "connected",
            "message": "Connected to JARVIS AI System",
            "client_id": client_id,
            "timestamp": datetime.now().isoformat()
        }, client_id)

        while True:
            # Receive message from client
            data = await websocket.receive_text()

            try:
                message_data = json.loads(data)
                message_type = message_data.get("type", "message")

                if message_type == "message":
                    # Handle regular message
                    user_message = message_data.get("content", "")
                    modality = message_data.get("modality", "text")
                    context = message_data.get("context", {})

                    # Process through the main agent
                    result = await agent.process_message(
                        user_input=user_message,
                        modality=modality,
                        context=context
                    )

                    # Send response back to client
                    await manager.send_personal_message({
                        "type": "response",
                        "content": result["response"],
                        "agent": result["agent"],
                        "timestamp": result["timestamp"],
                        "context": result.get("context"),
                        "metadata": result.get("metadata")
                    }, client_id)

                elif message_type == "ping":
                    # Handle ping/pong for connection health
                    await manager.send_personal_message({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }, client_id)

                elif message_type == "voice":
                    # Voice lifecycle signal from the client (listening started/stopped).
                    event = message_data.get("event", "")
                    logger.info(f"Voice event '{event}' from {client_id}")
                    await manager.send_personal_message({
                        "type": "voice",
                        "event": event,
                        "timestamp": datetime.now().isoformat()
                    }, client_id)

                elif message_type == "confirm":
                    # Confirm/deny a pending computer-control action.
                    token = message_data.get("token", "")
                    approved = bool(message_data.get("approved", True))
                    brain = getattr(agent, "brain", None)
                    system_agent = getattr(brain, "system_agent", None) if brain else None
                    if system_agent is None:
                        await manager.send_personal_message({
                            "type": "action",
                            "phase": "failed",
                            "message": "System Agent not available",
                            "timestamp": datetime.now().isoformat()
                        }, client_id)
                    else:
                        result = await system_agent.confirm_action(token, approved)
                        await manager.send_personal_message({
                            "type": "action",
                            "phase": "confirmed" if approved else "cancelled",
                            "action": result.get("metadata", {}).get("action"),
                            "message": result.get("response", ""),
                            "success": result.get("success", False),
                            "timestamp": datetime.now().isoformat()
                        }, client_id)

                elif message_type == "system_snapshot":
                    # Live system snapshot for the HUD
                    si = getattr(agent, "brain", None)
                    snapshot = await si.system_intelligence.get_live_snapshot() if si else {}
                    agents_status = await si.system_intelligence.get_agent_status() if si else {}
                    ollama_status = await si.system_intelligence.get_ollama_status() if si else {}

                    await manager.send_personal_message({
                        "type": "system_snapshot",
                        "snapshot": snapshot,
                        "agents": agents_status,
                        "ollama": ollama_status,
                        "timestamp": datetime.now().isoformat()
                    }, client_id)

                elif message_type == "get_status":
                    # Get system status
                    agent_status = await agent.get_status() if agent else {}
                    brain_status = {}
                    if hasattr(agent, 'brain') and agent.brain:
                        brain_status = await agent.brain.get_system_status()

                    await manager.send_personal_message({
                        "type": "status",
                        "agent": agent_status,
                        "brain": brain_status,
                        "connections": manager.get_connection_count(),
                        "timestamp": datetime.now().isoformat()
                    }, client_id)

                else:
                    # Unknown message type
                    await manager.send_personal_message({
                        "type": "error",
                        "message": f"Unknown message type: {message_type}",
                        "timestamp": datetime.now().isoformat()
                    }, client_id)

            except json.JSONDecodeError:
                # Handle plain text messages
                await manager.send_personal_message({
                    "type": "response",
                    "content": f"I received your message: {data}",
                    "agent": "jarvis",
                    "timestamp": datetime.now().isoformat()
                }, client_id)
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}", exc_info=True)
                await manager.send_personal_message({
                    "type": "error",
                    "message": "An error occurred while processing your message",
                    "details": str(e),
                    "timestamp": datetime.now().isoformat()
                }, client_id)

    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logger.info(f"Client {client_id} disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}", exc_info=True)
        manager.disconnect(client_id)


async def system_snapshot_broadcast_loop(brain, interval: float = 3.0):
    """Background loop: broadcast live system snapshot to all connected clients"""
    try:
        while True:
            await asyncio.sleep(interval)
            if manager.get_connection_count() == 0:
                continue
            try:
                si = brain.system_intelligence
                payload = {
                    "type": "system_snapshot",
                    "snapshot": await si.get_live_snapshot(),
                    "timestamp": datetime.now().isoformat()
                }
                await manager.broadcast(payload)
            except Exception as e:
                logger.error(f"Error broadcasting system snapshot: {e}")
    except asyncio.CancelledError:
        logger.info("System snapshot broadcast loop stopped")
        raise


@router.get("/status")
async def get_websocket_status():
    """
    Get WebSocket connection status
    """
    try:
        return {
            "active_connections": manager.get_connection_count(),
            "connections": manager.get_connection_info(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting WebSocket status: {e}")
        raise HTTPException(status_code=500, detail=str(e))