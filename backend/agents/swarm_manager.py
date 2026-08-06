"""
JARVIS AI Operating System - Swarm Manager
Coordinates multiple AI agents working together on complex tasks
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field

from core.personality import Personality
from memory.memory_manager import MemoryManager

if TYPE_CHECKING:
    from core.brain import JARVIS_Brain

logger = logging.getLogger(__name__)


class AgentType(str, Enum):
    """Types of agents in the swarm"""
    MAIN = "main_agent"
    CODING = "coding_agent"
    RESEARCH = "research_agent"
    SECURITY = "security_agent"
    SYSTEM = "system_agent"


class TaskPriority(str, Enum):
    """Task priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AgentMessage:
    """Message passed between agents"""
    sender: str
    recipient: str
    task_id: str
    action: str
    data: Any
    timestamp: datetime
    priority: TaskPriority = TaskPriority.MEDIUM


@dataclass
class SwarmTask:
    """Task to be executed by the swarm"""
    task_id: str
    description: str
    required_agents: List[AgentType]
    priority: TaskPriority
    dependencies: List[str] = None
    results: Dict[str, Any] = None
    status: str = "pending"  # pending, in_progress, completed, failed
    created_at: datetime = None
    completed_at: datetime = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.results is None:
            self.results = {}
        if self.created_at is None:
            self.created_at = datetime.now()


class SwarmManager:
    """
    Swarm Manager - Coordinates multiple AI agents working together
    Manages task distribution, inter-agent communication, and result synthesis
    """

    def __init__(self, brain: JARVIS_Brain):
        self.brain = brain
        self.logger = logging.getLogger(__name__)
        self.personality = Personality()
        self.memory_manager = MemoryManager()
        self.is_initialized = False

        # Agent registry
        self.agents: Dict[AgentType, Any] = {}
        self.agent_instances: Dict[str, Any] = {}

        # Task management
        self.task_queue: List[SwarmTask] = []
        self.active_tasks: Dict[str, SwarmTask] = {}
        self.completed_tasks: Dict[str, SwarmTask] = {}
        self.failed_tasks: Dict[str, SwarmTask] = {}

        # Communication
        self.message_queue: List[AgentMessage] = []
        self.message_history: List[AgentMessage] = []

        # Performance metrics
        self.metrics = {
            "tasks_processed": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "average_completion_time": 0.0,
            "messages_exchanged": 0
        }

    async def initialize(self):
        """Initialize the swarm manager"""
        try:
            self.logger.info("Initializing Swarm Manager...")
            await self.personality.initialize()
            await self.memory_manager.initialize()
            self.is_initialized = True
            self.logger.info("Swarm Manager initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Swarm Manager: {e}")
            raise

    async def register_agent(self, agent_type: AgentType, agent_instance: Any):
        """Register an agent with the swarm"""
        self.agents[agent_type] = agent_instance
        self.agent_instances[agent_type.value] = agent_instance
        self.logger.info(f"Registered agent: {agent_type.value}")

    async def unregister_agent(self, agent_type: AgentType):
        """Unregister an agent from the swarm"""
        if agent_type in self.agents:
            del self.agents[agent_type]
            del self.agent_instances[agent_type.value]
            self.logger.info(f"Unregistered agent: {agent_type.value}")

    async def select_agent_for_step(self, step):
        """Select the most appropriate agent for a given TaskStep.

        Returns (agent_instance, agent_key, reason)
        """
        # Candidate agents: prefer ones whose key matches step.agent_type
        candidates = []
        reason = ""
        if step.agent_type:
            # Exact match by registered agent key
            candidate = self.agent_instances.get(step.agent_type)
            if candidate:
                return candidate, step.agent_type, "explicit agent_type match"

        # Fallback: inspect agent specializations (if available) and pick the first that matches keywords
        keywords = [w for w in re.findall(r"\w+", step.description.lower())]

        for key, agent in list(self.agent_instances.items()):
            try:
                status = None
                if hasattr(agent, 'get_status'):
                    status = await agent.get_status()
                specializations = []
                if isinstance(status, dict):
                    specializations = status.get('specializations', [])
                # Agent name/type based match
                agent_name = getattr(agent, 'agent_name', '') or key
                if any(k in agent_name.lower() for k in keywords):
                    candidates.append((agent, key, 'name_match'))
                    continue
                if any(k in ' '.join(specializations).lower() for k in keywords):
                    candidates.append((agent, key, 'specialization_match'))
                    continue
            except Exception:
                continue

        # Prefer specialization matches, then name matches
        if candidates:
            selected = candidates[0]
            return selected[0], selected[1], selected[2]

        # As a last resort prefer MAIN agent if available
        main_agent = self.agent_instances.get(AgentType.MAIN.value)
        if main_agent:
            return main_agent, AgentType.MAIN.value, "fallback_to_main"

        return None, None, "no_agent_available"

    async def submit_task(
        self,
        description: str,
        required_agents: List[AgentType],
        priority: TaskPriority = TaskPriority.MEDIUM,
        dependencies: List[str] = None
    ) -> str:
        """
        Submit a task to the swarm for execution

        Args:
            description: Description of the task
            required_agents: List of agent types needed for the task
            priority: Priority level of the task
            dependencies: List of task IDs that must complete before this task

        Returns:
            Task ID for tracking
        """
        if not self.is_initialized:
            await self.initialize()

        task_id = f"task_{len(self.task_queue) + len(self.active_tasks) + len(self.completed_tasks)}_{int(datetime.now().timestamp())}"

        task = SwarmTask(
            task_id=task_id,
            description=description,
            required_agents=required_agents,
            priority=priority,
            dependencies=dependencies or []
        )

        self.task_queue.append(task)
        self.logger.info(f"Submitted task {task_id}: {description}")

        # Start processing the queue
        asyncio.create_task(self._process_task_queue())

        return task_id


    async def execute_plan(self, plan) -> str:
        """
        Execute an ExecutionPlan by dispatching steps to registered agents.

        Args:
            plan: An ExecutionPlan instance from core.planner

        Returns:
            Synthesized string response combining agent results
        """
        if not self.is_initialized:
            await self.initialize()

        try:
            responses = []

            for step in plan.steps:
                # Agent selection with reasoning and fallback
                selected_agent, selected_key, selection_reason = await self.select_agent_for_step(step)

                # main_agent steps should be skipped as orchestration is handled by brain
                if selected_key == AgentType.MAIN.value:
                    self.logger.debug(
                        f"Skipping main_agent step '{step.id}' (orchestration already handled by brain)"
                    )
                    continue

                if selected_agent is None:
                    self.logger.warning(
                        f"No suitable agent found for step '{step.id}', skipping"
                    )
                    continue

                # Record last agent selection to the brain for observability
                try:
                    if self.brain is not None:
                        self.brain.last_agent_selection = {
                            "task_id": getattr(plan, 'request_id', None),
                            "step_id": step.id,
                            "agent_key": selected_key,
                            "reason": selection_reason,
                            "timestamp": datetime.now().isoformat()
                        }
                except Exception:
                    pass

                context = {
                    "step_id": step.id,
                    "description": step.description,
                    "swarm_context": True
                }

                if hasattr(selected_agent, "process_request"):
                    result = await selected_agent.process_request(
                        request=plan.original_request,
                        context=context
                    )
                elif hasattr(selected_agent, "process_message"):
                    result = await selected_agent.process_message(
                        user_input=plan.original_request,
                        modality="text",
                        context=context
                    )
                else:
                    self.logger.warning(
                        f"Agent '{selected_key}' has no process_request/process_message"
                    )
                    continue

                if isinstance(result, dict):
                    response_text = result.get("response", "")
                    if response_text:
                        responses.append(response_text)
                    if result.get("error"):
                        self.logger.error(
                            f"Step '{step.id}' via '{selected_key}' failed: {response_text}"
                        )
                else:
                    responses.append(str(result))

            if responses:
                return "\n\n".join(responses)

            # Fallback: use the brain's model router with the plan prompt
            if self.brain is not None:
                model_selection = await self.brain.model_router.select_model(
                    task_type=plan.task_type,
                    complexity=plan.complexity,
                    context=[]
                )
                return await self.brain.model_router.generate(
                    prompt=plan.prompt,
                    model=model_selection.model,
                    temperature=model_selection.temperature,
                    max_tokens=model_selection.max_tokens
                )

            return "I could not complete the request because no agents were available."

        except Exception as e:
            self.logger.error(f"Error executing plan: {e}", exc_info=True)
            return f"I encountered an error while processing your request: {e}"

    async def _process_task_queue(self):
        """Process tasks in the queue based on priority and dependencies"""
        while self.task_queue or self.active_tasks:
            # Sort queue by priority (critical first)
            priority_weights = {
                TaskPriority.CRITICAL: 4,
                TaskPriority.HIGH: 3,
                TaskPriority.MEDIUM: 2,
                TaskPriority.LOW: 1
            }

            self.task_queue.sort(key=lambda t: priority_weights[t.priority], reverse=True)

            # Process tasks that have no dependencies or whose dependencies are met
            ready_tasks = []
            for task in self.task_queue[:]:  # Copy list to avoid modification during iteration
                if self._are_dependencies_met(task):
                    ready_tasks.append(task)
                    self.task_queue.remove(task)

            # Execute ready tasks (limited concurrency)
            for task in ready_tasks[:3]:  # Limit to 3 concurrent tasks
                if task.task_id not in self.active_tasks:
                    asyncio.create_task(self._execute_task(task))

                # Small delay to prevent overwhelming the system
                await asyncio.sleep(0.1)

            # Wait a bit before checking again
            await asyncio.sleep(1)

    def _are_dependencies_met(self, task: SwarmTask) -> bool:
        """Check if all dependencies for a task are completed"""
        for dep_id in task.dependencies:
            if dep_id not in self.completed_tasks:
                return False
        return True

    async def _execute_task(self, task: SwarmTask):
        """Execute a task using the required agents"""
        self.active_tasks[task.task_id] = task
        task.status = "in_progress"

        start_time = datetime.now()

        try:
            self.logger.info(f"Executing task {task.task_id}: {task.description}")

            # Check if all required agents are available
            missing_agents = [agent for agent in task.required_agents if agent not in self.agents]
            if missing_agents:
                raise Exception(f"Missing required agents: {[a.value for a in missing_agents]}")

            # For now, we'll execute tasks sequentially with the first available agent
            # In a more sophisticated implementation, we'd distribute subtasks
            primary_agent_type = task.required_agents[0]
            agent = self.agents[primary_agent_type]

            # Execute the task using the agent
            result = await agent.process_request(
                request=task.description,
                context={"task_id": task.task_id, "swarm_context": True}
            )

            # Store result
            task.results = {
                "agent_used": primary_agent_type.value,
                "response": result.get("response", ""),
                "metadata": result.get("metadata", {}),
                "success": not result.get("error", False)
            }

            task.status = "completed" if task.results["success"] else "failed"
            task.completed_at = datetime.now()

            # Move to appropriate collection
            if task.status == "completed":
                self.completed_tasks[task.task_id] = task
                self.metrics["successful_tasks"] += 1
            else:
                self.failed_tasks[task.task_id] = task
                self.metrics["failed_tasks"] += 1

            self.metrics["tasks_processed"] += 1

            # Calculate average completion time
            completion_time = (task.completed_at - start_time).total_seconds()
            total_time = self.metrics["average_completion_time"] * (self.metrics["tasks_processed"] - 1) + completion_time
            self.metrics["average_completion_time"] = total_time / self.metrics["tasks_processed"]

            self.logger.info(f"Completed task {task.task_id} with status: {task.status}")

        except Exception as e:
            self.logger.error(f"Error executing task {task.task_id}: {e}", exc_info=True)
            task.status = "failed"
            task.completed_at = datetime.now()
            task.results = {
                "error": str(e),
                "success": False
            }
            self.failed_tasks[task.task_id] = task
            self.metrics["failed_tasks"] += 1
            self.metrics["tasks_processed"] += 1

        finally:
            # Remove from active tasks
            if task.task_id in self.active_tasks:
                del self.active_tasks[task.task_id]

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a specific task"""
        # Check active tasks
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            return {
                "task_id": task.task_id,
                "description": task.description,
                "status": task.status,
                "progress": "in_progress",
                "created_at": task.created_at.isoformat() if task.created_at else None
            }

        # Check completed tasks
        if task_id in self.completed_tasks:
            task = self.completed_tasks[task_id]
            return {
                "task_id": task.task_id,
                "description": task.description,
                "status": task.status,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "result": task.results
            }

        # Check failed tasks
        if task_id in self.failed_tasks:
            task = self.failed_tasks[task_id]
            return {
                "task_id": task.task_id,
                "description": task.description,
                "status": task.status,
                "failed_at": task.completed_at.isoformat() if task.completed_at else None,
                "error": task.results.get("error", "Unknown error")
            }

        # Check queued tasks
        for task in self.task_queue:
            if task.task_id == task_id:
                return {
                    "task_id": task.task_id,
                    "description": task.description,
                    "status": task.status,
                    "position": self.task_queue.index(task) + 1,
                    "created_at": task.created_at.isoformat() if task.created_at else None
                }

        return None

    async def get_swarm_status(self) -> Dict[str, Any]:
        """Get overall status of the swarm"""
        return {
            "initialized": self.is_initialized,
            "registered_agents": [agent_type.value for agent_type in self.agents.keys()],
            "queue_length": len(self.task_queue),
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "failed_tasks": len(self.failed_tasks),
            "metrics": self.metrics.copy(),
            "agents_status": {
                agent_type.value: await agent.get_status()
                if hasattr(agent, 'get_status') else {"status": "unknown"}
                for agent_type, agent in self.agents.items()
            }
        }

    async def shutdown(self):
        """Shutdown the swarm manager"""
        self.logger.info("Shutting down Swarm Manager")
        self.is_initialized = False

        # Shutdown all agents
        for agent in self.agents.values():
            if hasattr(agent, 'shutdown'):
                await agent.shutdown()