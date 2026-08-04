"""
JARVIS AI Operating System - Chat API
Handles chat-based interactions with the AI system
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
from datetime import datetime

from agents.main_agent import MainAgent
from api.dependencies import get_brain, get_main_agent

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    modality: str = "text"
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    response: str
    agent: str
    timestamp: str
    context: Optional[Any] = None
    metadata: Optional[Dict[str, Any]] = None


@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    agent: MainAgent = Depends(get_main_agent)
):
    """
    Send a message to JARVIS and get a response
    """
    try:
        logger.info(f"Received chat message: {request.message[:100]}...")

        # Process the message through the main agent
        result = await agent.process_message(
            user_input=request.message,
            modality=request.modality,
            context=request.context
        )

        return ChatResponse(
            response=result["response"],
            agent=result["agent"],
            timestamp=result["timestamp"],
            context=result.get("context"),
            metadata=result.get("metadata")
        )

    except Exception as e:
        logger.error(f"Error processing chat message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_chat_history(agent: MainAgent = Depends(get_main_agent)):
    """
    Get recent chat history
    """
    try:
        # In a full implementation, this would retrieve from memory
        # For now, we'll return a placeholder
        return {
            "message": "Chat history feature coming soon",
            "status": "not_implemented"
        }
    except Exception as e:
        logger.error(f"Error retrieving chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_chat_status(agent: MainAgent = Depends(get_main_agent)):
    """
    Get the status of the chat system
    """
    try:
        agent_status = await agent.get_status()
        brain_status = {}
        if hasattr(agent, 'brain') and agent.brain:
            brain_status = await agent.brain.get_system_status()

        return {
            "agent": agent_status,
            "brain": brain_status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting chat status: {e}")
        raise HTTPException(status_code=500, detail=str(e))