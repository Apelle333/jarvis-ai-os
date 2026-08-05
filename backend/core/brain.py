"""
JARVIS AI Operating System - Central Brain
Main intelligence system that coordinates all components
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

from .settings import settings
from .planner import Planner, TaskType, ComplexityLevel
from .model_router import ModelRouter
from .personality import Personality
from agents.swarm_manager import SwarmManager, AgentType
from agents.main_agent import MainAgent
from agents.coding_agent import CodingAgent
from agents.research_agent import ResearchAgent
from agents.security_agent import SecurityAgent
from agents.system_agent import SystemAgent
from core.command_detector import detect_computer_command
from memory.memory_manager import MemoryManager
from tools.system_monitor import SystemMonitor
from tools.system_intelligence import SystemIntelligence


logger = logging.getLogger(__name__)


class SystemState(str, Enum):
    """System operational states"""
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    EXECUTING = "executing"
    SPEAKING = "speaking"
    ERROR = "error"


class CoreStatus(str, Enum):
    """Runtime core readiness states"""
    READY = "ready"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class JARVIS_Brain:
    """
    Central intelligence system of JARVIS
    Coordinates all components and handles the main processing loop
    """

    def __init__(self):
        self.state = SystemState.IDLE
        self.settings = settings

        self.planner = Planner()
        self.model_router = ModelRouter()
        self.personality = Personality()
        self.swarm_manager = SwarmManager(brain=self)
        self.memory_manager = MemoryManager()
        self.system_monitor = SystemMonitor()
        self.system_intelligence = SystemIntelligence(brain=self)
        self.system_agent: Optional[SystemAgent] = None

        self.is_initialized = False
        self.is_shutting_down = False
        self.core_status = CoreStatus.UNAVAILABLE
        self.core_status_reasons: List[str] = []
        self.core_component_health: Dict[str, Any] = {}

        self.logger = logging.getLogger(__name__)

        self.start_time = datetime.now()
        self.request_count = 0
        self.error_count = 0

        logger.info("JARVIS Brain initialized")


    async def initialize(self):
        """Initialize all components"""
        if self.is_initialized:
            self.logger.info("JARVIS Brain already initialized")
            return

        try:
            self.logger.info("Initializing JARVIS components...")

            # Initialize memory
            await self.memory_manager.initialize()

            # Initialize system monitor
            try:
                await self.system_monitor.initialize()
                await self.system_monitor.start()
            except Exception as monitor_error:
                self.logger.warning(
                    "System Monitor failed to start (continuing without it): %s",
                    monitor_error,
                )

            # Check Ollama models (degrade gracefully if Ollama is unavailable)
            try:
                models = [
                    self.settings.default_model,
                    self.settings.coder_model,
                    self.settings.reasoning_model
                ]

                missing_models = []
                for model in models:
                    available = await self.model_router.is_model_available(model)
                    if not available:
                        missing_models.append(model)

                if missing_models:
                    # Log missing models but do NOT auto-pull them. Pulling
                    # multi-GB models during startup can block and consume
                    # resources; preserve manual model management instead.
                    self.logger.warning(
                        "Ollama models missing: %s. Not auto-pulling during startup.",
                        ", ".join(missing_models),
                    )
            except Exception as model_error:
                self.logger.error(
                    "Ollama model verification failed "
                    f"(continuing without it): {model_error}"
                )

            # Initialize personality
            await self.personality.initialize()

            # Register specialist agents with the swarm
            agent_errors: List[str] = []
            try:
                await self._register_agents()
            except Exception as agent_error:
                agent_errors.append(str(agent_error))
                self.logger.warning(
                    "Agent registration incomplete (continuing in degraded mode): %s",
                    agent_error,
                )

            self.is_initialized = True
            self._evaluate_core_status(agent_errors=agent_errors)
            self.logger.info(
                "JARVIS Brain initialized successfully"
            )

        except Exception as e:
            self.logger.error(
                f"Failed to initialize JARVIS Brain: {e}",
                exc_info=True
            )
            self.state = SystemState.ERROR
            self.core_status = CoreStatus.UNAVAILABLE
            self.core_status_reasons = [str(e)]
            raise


    async def _register_agents(self):
        """Register all specialist agents with the swarm"""
        agent_instances = {
            AgentType.MAIN: MainAgent(brain=self),
            AgentType.CODING: CodingAgent(brain=self),
            AgentType.RESEARCH: ResearchAgent(brain=self),
            AgentType.SECURITY: SecurityAgent(brain=self),
            AgentType.SYSTEM: SystemAgent(brain=self),
        }

        for agent_type, instance in agent_instances.items():
            await self.swarm_manager.register_agent(agent_type, instance)
            if agent_type == AgentType.SYSTEM:
                self.system_agent = instance

        self.logger.info(
            f"Registered {len(agent_instances)} agents with the swarm"
        )

    def _collect_core_health(self) -> Dict[str, Any]:
        """Collect health information for core subcomponents."""
        health: Dict[str, Any] = {}

        sqlite_ok = bool(
            self.memory_manager.sqlite_memory is not None
            and getattr(self.memory_manager.sqlite_memory, "is_initialized", False)
        )
        health["sqlite_memory"] = {
            "available": sqlite_ok,
            "detail": "initialized" if sqlite_ok else "unavailable",
        }

        vector_ok = bool(
            self.memory_manager.vector_memory is not None
            and getattr(self.memory_manager.vector_memory, "is_initialized", False)
        )
        health["vector_memory"] = {
            "available": vector_ok,
            "detail": "initialized" if vector_ok else "unavailable",
        }

        monitor_ok = bool(
            self.system_monitor is not None
            and getattr(self.system_monitor, "is_initialized", False)
        )
        health["system_monitor"] = {
            "available": monitor_ok,
            "detail": "running" if monitor_ok else "unavailable",
        }

        available_models = getattr(self.model_router, "available_models", {})
        model_names = [name for name, ok in available_models.items() if ok]
        missing_models = [name for name, ok in available_models.items() if not ok]
        health["ollama"] = {
            "available": bool(model_names),
            "available_models": model_names,
            "missing_models": missing_models,
            "detail": (
                "models available" if model_names else "no configured models available"
            ),
        }

        registered_agents = len(self.swarm_manager.agents)
        expected_agents = len(AgentType)
        health["agent_registration"] = {
            "available": registered_agents == expected_agents,
            "registered_count": registered_agents,
            "expected_count": expected_agents,
            "detail": (
                "all agents registered"
                if registered_agents == expected_agents
                else "partial agent registration"
            ),
        }

        return health

    def _evaluate_core_status(self, agent_errors: Optional[List[str]] = None) -> None:
        """Evaluate the core runtime status after initialization."""
        health = self._collect_core_health()
        self.core_component_health = health

        reasons: List[str] = []
        if agent_errors:
            reasons.extend(agent_errors)

        if not health["sqlite_memory"]["available"]:
            self.core_status = CoreStatus.UNAVAILABLE
            reasons.append("SQLite memory unavailable")
        else:
            if not health["system_monitor"]["available"]:
                reasons.append("System Monitor unavailable")
            if not health["vector_memory"]["available"]:
                reasons.append("Vector memory unavailable")
            if not health["ollama"]["available"]:
                reasons.append("Ollama models unavailable")
            if not health["agent_registration"]["available"]:
                reasons.append("Agent registration incomplete")

            self.core_status = CoreStatus.DEGRADED if reasons else CoreStatus.READY

        self.core_status_reasons = reasons

    async def shutdown(self):
        """Shutdown all components gracefully"""
        if self.is_shutting_down:
            self.logger.info("JARVIS Brain shutdown already in progress")
            return

        self.is_shutting_down = True
        try:
            self.logger.info("Shutting down JARVIS components...")

            try:
                await self.system_monitor.stop()
            except Exception as monitor_error:
                self.logger.warning(
                    "System Monitor shutdown failed: %s",
                    monitor_error,
                )

            try:
                await self.memory_manager.shutdown()
            except Exception as memory_error:
                self.logger.warning(
                    "Memory Manager shutdown failed: %s",
                    memory_error,
                )

            try:
                await self.model_router.cleanup()
            except Exception as router_error:
                self.logger.warning(
                    "Model Router cleanup failed: %s",
                    router_error,
                )

            self.is_initialized = False
            self.core_status = CoreStatus.UNAVAILABLE
            self.core_status_reasons = ["shutdown"]
            self.logger.info(
                "JARVIS Brain shutdown complete"
            )

        except Exception as e:
            self.logger.error(
                f"Error during shutdown: {e}"
            )
        finally:
            self.is_shutting_down = False


    async def process_input(
        self,
        user_input: str,
        modality: str = "text"
    ) -> str:

        self.request_count += 1
        self.state = SystemState.PROCESSING

        try:
            self.logger.info(
                f"Processing input ({modality}): {user_input[:100]}"
            )

            await self.memory_manager.store_conversation(
                role="user",
                content=user_input,
                modality=modality,
                timestamp=datetime.now()
            )

            context = await self.memory_manager.get_recent_context(
                limit=10
            )

            # ---- Computer Control fast-path --------------------------------
            # Deterministic, bilingual intent detection: known commands are
            # executed directly by the System Agent (no LLM round-trip).
            if self.system_agent is not None and settings.computer_control_enabled:
                intent = detect_computer_command(
                    user_input,
                    pending=self.system_agent.pending_action
                )
                if intent is not None:
                    self.state = SystemState.EXECUTING
                    result = await self.system_agent.execute_computer_request(
                        user_input, intent=intent
                    )
                    response = await self.personality.apply_personality(
                        response=result["response"],
                        context=context,
                        user_input=user_input
                    )
                    await self.memory_manager.store_conversation(
                        role="assistant",
                        content=response,
                        modality="text",
                        timestamp=datetime.now(),
                        metadata={
                            "computer_control": True,
                            "action": intent.action,
                            "category": intent.category,
                            "target": intent.target,
                            "success": result.get("success", False),
                            "needs_confirmation": result.get("needs_confirmation", False),
                        }
                    )
                    self.state = SystemState.IDLE
                    return response

            plan = await self.planner.create_plan(
                user_input=user_input,
                context=context,
                personality_state=await self.personality.get_current_state()
            )

            model_selection = await self.model_router.select_model(
                task_type=plan.task_type,
                complexity=plan.complexity,
                context=context
            )

            if plan.task_type == TaskType.SYSTEM_ANALYSIS:
                result = await self._handle_system_analysis(
                    user_input=user_input,
                    context=context
                )

            elif plan.requires_agents:
                result = await self.swarm_manager.execute_plan(plan)

            else:
                result = await self.model_router.generate(
                    prompt=plan.prompt,
                    model=model_selection.model,
                    context=context,
                    temperature=model_selection.temperature,
                    max_tokens=model_selection.max_tokens
                )

            response = await self.personality.apply_personality(
                response=result,
                context=context,
                user_input=user_input
            )

            await self.memory_manager.store_conversation(
                role="assistant",
                content=response,
                modality="text",
                timestamp=datetime.now()
            )

            self.state = SystemState.IDLE

            return response

        except Exception as e:
            self.error_count += 1
            self.state = SystemState.ERROR

            self.logger.error(
                f"Error processing input: {e}",
                exc_info=True
            )

            return await self.personality.handle_error(str(e))


    async def _handle_system_analysis(
        self,
        user_input: str,
        context: list
    ) -> str:
        """Route system/state questions through SystemIntelligence (real data)"""
        text = user_input.lower()
        si = self.system_intelligence

        data = {
            "status": await si.get_system_status()
        }

        if "module" in text or "component" in text:
            data["modules"] = await si.get_active_modules()

        if "process" in text:
            data["processes"] = await si.get_running_processes(limit=8)

        summary = self._format_system_summary(data)

        simple_lookup = any(
            kw in text
            for kw in [
                "which model",
                "what model",
                "are you ok",
                "are you up",
                "what is running",
                "what's running",
                "how are you running",
                "how is your",
                "is the server",
                "do you have a gpu",
                "how much ram",
                "your status",
                "your health",
                "what agents",
                "what modules",
                "which modules",
                "how many models",
            ]
        )

        if simple_lookup:
            response = summary
        else:
            compact = self._format_system_summary(data, compact=True)
            prompt = (
                "You are JARVIS, the user's personal AI system. Answer the "
                f"user's question about their machine using ONLY the real "
                "data provided below. Do not invent numbers.\n\n"
                f"User question: {user_input}\n\n"
                f"Live system data:\n{compact}\n\n"
                "Rules:\n"
                "- Only report facts present in the data.\n"
                "- If the question asks for analysis, interpret the numbers.\n"
                "- Be concise and warm. Maximum 6 short sentences.\n"
            )
            model_selection = await self.model_router.select_model(
                task_type=TaskType.SYSTEM_ANALYSIS,
                complexity=ComplexityLevel.MODERATE,
                context=context,
            )
            response = await self.model_router.generate(
                prompt=prompt,
                model=model_selection.model,
                context=context,
                temperature=model_selection.temperature,
                max_tokens=400,
            )
            if not response or not response.strip():
                logger.warning(
                    "LLM returned empty system analysis, falling back to raw summary"
                )
                response = summary
            else:
                await si.store_system_scan(summary)

        return response

    def _format_system_summary(self, data: dict, compact: bool = False) -> str:
        """Render live system data into a compact readable summary"""
        lines: list = []
        status = data.get("status", {})

        lines.append(f"Application: {status.get('application', 'unknown')}")
        lines.append(f"Brain state: {status.get('brain_state', 'unknown')}")
        uptime = float(status.get("uptime_seconds") or 0)
        lines.append(
            f"Uptime: {int(uptime)}s ({uptime / 3600:.1f}h) | "
            f"Requests: {status.get('request_count', 0)} | "
            f"Errors: {status.get('error_count', 0)}"
        )

        hw = status.get("hardware", {})
        cpu = hw.get("cpu", {})
        mem = hw.get("memory", {})
        disk = hw.get("disk", {})
        lines.append(
            f"CPU: {cpu.get('usage_percent', 0)}% used across "
            f"{cpu.get('cores', '?')} cores @ {cpu.get('frequency_mhz', '?')} MHz"
        )
        lines.append(
            f"RAM: {mem.get('used_human', 'N/A')} of "
            f"{mem.get('total_human', 'N/A')} used ({mem.get('percent', 0)}%)"
        )
        lines.append(
            f"Disk: {disk.get('free_human', 'N/A')} free "
            f"({disk.get('percent', 0)}% used)"
        )
        gpu = hw.get("gpu_summary")
        if gpu:
            lines.append(
                f"GPU: {gpu.get('name')} at {gpu.get('utilization_percent', 0)}% "
                f"util, {gpu.get('memory_used_mb', 0):.0f}/"
                f"{gpu.get('memory_total_mb', 0):.0f} MB, "
                f"{gpu.get('temperature_c', 0):.0f} C"
            )
        else:
            lines.append("GPU: none detected")
        lines.append(
            f"Host: {hw.get('host', '?')} "
            f"({hw.get('platform', '')} {hw.get('architecture', '')})"
        )

        ollama = status.get("ollama", {})
        if ollama.get("server_running"):
            lines.append(
                f"Ollama: ONLINE at {ollama.get('server_url')} - "
                f"{len(ollama.get('model_names', []))} models"
            )
            names = ollama.get("model_names", [])
            if names:
                lines.append("Models: " + ", ".join(names))
            loaded = ollama.get("loaded_models", [])
            if loaded:
                lines.append("Loaded now: " + ", ".join(loaded))
        else:
            lines.append(
                f"Ollama: OFFLINE ({ollama.get('error') or 'unreachable'})"
            )

        agents = status.get("agents", {})
        agent_list = agents.get("agents", [])
        if agent_list:
            lines.append(
                f"Agents ({agents.get('active', 0)}/{len(agent_list)} active): "
                + ", ".join(a.get("name", "?") for a in agent_list)
            )
        else:
            lines.append("Agents: none registered")

        mem_status = status.get("memory", {})
        st = mem_status.get("short_term", {})
        lt = mem_status.get("long_term", {})
        lines.append(
            f"Memory: initialized={mem_status.get('is_initialized', False)} "
            f"conversations={st.get('conversations_count', '?')} "
            f"vector_docs={lt.get('count', lt.get('document_count', '?'))}"
        )

        for m in data.get("modules", {}).get("modules", []):
            if compact and m.get("category") not in ("Core", "AI"):
                continue
            lines.append(
                f"[{m.get('category')}] {m.get('name')}: "
                f"{m.get('status')} - {m.get('detail')}"
            )

        for p in data.get("processes", {}).get("top_by_cpu", [])[:5]:
            lines.append(
                f"TOP CPU: {p.get('name')} ({p.get('cpu_percent')}%)"
            )

        return "\n".join(lines)

    async def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""

        uptime = datetime.now() - self.start_time

        return {
            "state": self.state.value,
            "uptime_seconds": uptime.total_seconds(),
            "request_count": self.request_count,
            "error_count": self.error_count,
            "memory_stats": await self.memory_manager.get_stats(),
            "system_stats": await self.system_monitor.get_current_stats(),
            "model_info": await self.model_router.get_available_models()
        }


    def set_state(self, state: SystemState):
        """Set system state"""

        old_state = self.state
        self.state = state

        self.logger.info(
            f"State changed: {old_state.value} -> {state.value}"
        )