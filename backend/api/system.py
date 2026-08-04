"""
JARVIS AI Operating System - System Intelligence API
Read-only endpoints exposing real system data for the HUD / voice control
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from core.brain import JARVIS_Brain
from tools.system_intelligence import SystemIntelligence
from api.dependencies import get_brain

logger = logging.getLogger(__name__)

router = APIRouter()


def _si(brain: JARVIS_Brain) -> SystemIntelligence:
    return brain.system_intelligence


def _system_agent(brain: JARVIS_Brain):
    """The shared System Agent (computer-control orchestrator)."""
    return getattr(brain, "system_agent", None)


class ConfirmActionRequest(BaseModel):
    token: str
    approved: bool = True


@router.get("/status")
async def system_status(brain: JARVIS_Brain = Depends(get_brain)):
    """Combined status of the whole system"""
    try:
        return await _si(brain).get_system_status()
    except Exception as e:
        logger.error(f"Error getting system status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/modules")
async def system_modules(brain: JARVIS_Brain = Depends(get_brain)):
    """Active JARVIS modules and their status"""
    try:
        return await _si(brain).get_active_modules()
    except Exception as e:
        logger.error(f"Error getting modules: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hardware")
async def system_hardware(brain: JARVIS_Brain = Depends(get_brain)):
    """Real hardware info (CPU, GPU, RAM, disk, network)"""
    try:
        return await _si(brain).get_hardware_info()
    except Exception as e:
        logger.error(f"Error getting hardware info: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents")
async def system_agents(brain: JARVIS_Brain = Depends(get_brain)):
    """Status of all registered agents"""
    try:
        return await _si(brain).get_agent_status()
    except Exception as e:
        logger.error(f"Error getting agent status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ollama")
async def system_ollama(brain: JARVIS_Brain = Depends(get_brain)):
    """Ollama server and model status"""
    try:
        return await _si(brain).get_ollama_status()
    except Exception as e:
        logger.error(f"Error getting Ollama status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory")
async def system_memory(brain: JARVIS_Brain = Depends(get_brain)):
    """Memory system status"""
    try:
        return await _si(brain).get_memory_status()
    except Exception as e:
        logger.error(f"Error getting memory status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def system_health(brain: JARVIS_Brain = Depends(get_brain)):
    """Application health derived from real module states"""
    try:
        return await _si(brain).get_application_health()
    except Exception as e:
        logger.error(f"Error getting application health: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/processes")
async def system_processes(brain: JARVIS_Brain = Depends(get_brain)):
    """Top running processes by CPU and memory"""
    try:
        return await _si(brain).get_running_processes(limit=10)
    except Exception as e:
        logger.error(f"Error getting processes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/snapshot")
async def system_snapshot(brain: JARVIS_Brain = Depends(get_brain)):
    """Lightweight live snapshot for HUD updates"""
    try:
        return await _si(brain).get_live_snapshot()
    except Exception as e:
        logger.error(f"Error getting live snapshot: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scan")
async def system_scan(brain: JARVIS_Brain = Depends(get_brain)):
    """Most recent system scan stored in memory"""
    try:
        return {"scan": await _si(brain).get_last_system_scan()}
    except Exception as e:
        logger.error(f"Error getting last scan: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Computer-control actions (confirmation + HUD feed)
# ---------------------------------------------------------------------------

@router.get("/actions/recent")
async def recent_actions(brain: JARVIS_Brain = Depends(get_brain)):
    """Most recent computer-control actions (for the HUD activity feed)."""
    try:
        agent = _system_agent(brain)
        if agent is None:
            return {"actions": [], "count": 0}
        return {"actions": agent.get_action_log(), "count": len(agent.get_action_log())}
    except Exception as e:
        logger.error(f"Error getting recent actions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/actions/pending")
async def pending_action(brain: JARVIS_Brain = Depends(get_brain)):
    """The action currently awaiting user confirmation, if any."""
    try:
        agent = _system_agent(brain)
        if agent is None:
            return {"pending": None}
        return {"pending": agent.get_pending_action()}
    except Exception as e:
        logger.error(f"Error getting pending action: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/actions/confirm")
async def confirm_action(
    request: ConfirmActionRequest,
    brain: JARVIS_Brain = Depends(get_brain),
):
    """
    Confirm or deny a pending computer-control action by token.
    """
    try:
        agent = _system_agent(brain)
        if agent is None:
            raise HTTPException(status_code=500, detail="System Agent not available")
        result = await agent.confirm_action(request.token, request.approved)
        return {
            "success": result.get("success", False),
            "response": result.get("response", ""),
            "data": result.get("data", {}),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error confirming action: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
