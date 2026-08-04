"""
JARVIS AI Operating System - Shared API Dependencies
Central location for the single brain/main_agent instances shared across routers
"""

import logging
from typing import Optional

from fastapi import Depends

from agents.main_agent import MainAgent
from core.brain import JARVIS_Brain

logger = logging.getLogger(__name__)

# Shared instances populated during application lifespan
brain: Optional[JARVIS_Brain] = None
main_agent: Optional[MainAgent] = None


def set_brain(instance: JARVIS_Brain):
    """Set the shared brain instance (called from lifespan)"""
    global brain
    brain = instance


def get_brain() -> JARVIS_Brain:
    """Dependency to get the shared brain instance"""
    global brain
    if brain is None:
        brain = JARVIS_Brain()
    return brain


def get_main_agent(instance: JARVIS_Brain = Depends(get_brain)) -> MainAgent:
    """Dependency to get the shared main agent instance"""
    global main_agent
    if main_agent is None:
        main_agent = MainAgent(brain=instance)
    return main_agent
