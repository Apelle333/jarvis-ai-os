"""
JARVIS AI Operating System - Main Agent
Primary conversational agent and user interface
"""

from __future__ import annotations

import asyncio
import logging
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from datetime import datetime

from core.personality import Personality
from memory.memory_manager import MemoryManager

if TYPE_CHECKING:
    from core.brain import JARVIS_Brain

logger = logging.getLogger(__name__)


class MainAgent:
    """
    Main agent - the primary interface for user interaction
    Acts as the central conversational agent that delegates to specialists
    """

    def __init__(self, brain: JARVIS_Brain):
        self.brain = brain
        self.logger = logging.getLogger(__name__)
        self.personality = Personality()
        # The Brain owns the single shared memory system. Creating another
        # manager here duplicated SQLite/Chroma initialization and separated
        # the agent's context from the conversations stored by the Brain.
        self.memory_manager = brain.memory_manager
        self.is_initialized = False
        self.last_error: Optional[str] = None

        # Agent metadata
        self.agent_id = "main_agent"
        self.agent_name = "JARVIS"
        self.agent_type = "conversational"
        self.capabilities = [
            "general_conversation",
            "task_coordination",
            "user_interaction",
            "intent_understanding",
            "response_personalization"
        ]

    async def initialize(self):
        """Initialize the main agent"""
        try:
            self.logger.info("Initializing Main Agent...")
            await self.personality.initialize()
            if not getattr(self.memory_manager, "is_initialized", False):
                await self.memory_manager.initialize()
            self.is_initialized = True
            self.logger.info("Main Agent initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Main Agent: {e}")
            raise

    async def process_message(
        self,
        user_input: str,
        modality: str = "text",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process incoming user message and generate response

        Args:
            user_input: The user's input message
            modality: Input modality (text, voice, vision)
            context: Additional context information

        Returns:
            Dictionary containing response and metadata
        """
        if not self.is_initialized:
            await self.initialize()

        try:
            self.logger.info(f"Main Agent processing {modality} input: {user_input[:100]}...")

            # Delegate to the brain, which handles planning, model routing,
            # swarm dispatch, personality, and memory storage
            response = await self.brain.process_input(user_input, modality)

            # Get updated context for response
            updated_context = await self.memory_manager.get_recent_context(limit=10)

            return {
                "response": response,
                "agent": self.agent_id,
                "timestamp": datetime.now().isoformat(),
                "context": updated_context,
                "metadata": {
                    "modality": modality,
                    "processed_by": "main_agent",
                    "personality_applied": True
                }
            }

        except Exception as e:
            self.last_error = str(e)
            self.logger.error(f"Error in Main Agent processing: {e}", exc_info=True)
            error_response = await self.personality.handle_error(str(e))
            return {
                "response": error_response,
                "agent": self.agent_id,
                "timestamp": datetime.now().isoformat(),
                "error": True,
                "metadata": {
                    "modality": modality,
                    "processed_by": "main_agent",
                    "error": str(e)
                }
            }

    async def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "agent_type": self.agent_type,
            "is_initialized": self.is_initialized,
            "capabilities": self.capabilities,
            "health_state": "healthy" if self.is_initialized and not self.last_error else ("degraded" if self.last_error else "standby"),
            "last_error": self.last_error,
            "last_activity": datetime.now().isoformat()
        }

    async def shutdown(self):
        """Shutdown the agent"""
        self.logger.info("Shutting down Main Agent")
        self.is_initialized = False
        # Cleanup any resources if needed
