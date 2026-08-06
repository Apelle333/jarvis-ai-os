"""
JARVIS AI Operating System - Planner Module
Responsible for breaking down user requests into executable plans
"""

import asyncio
import logging
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class TaskType(str, Enum):
    GENERAL_QUESTION = "general_question"
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    DEBUGGING = "debugging"
    ARCHITECTURE_DESIGN = "architecture_design"
    REFACTORING = "refactoring"
    DOCUMENTATION = "documentation"
    RESEARCH = "research"
    FILE_OPERATION = "file_operation"
    SYSTEM_COMMAND = "system_command"
    AUTOMATION = "automation"
    CREATIVE_WRITING = "creative_writing"
    ANALYSIS = "analysis"
    PLANNING = "planning"
    SYSTEM_ANALYSIS = "system_analysis"


class ComplexityLevel(str, Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    EXPERT = "expert"


@dataclass
class TaskStep:
    id: str
    description: str
    agent_type: Optional[str] = None
    tool_required: Optional[str] = None
    dependencies: Optional[List[str]] = None
    estimated_time: float = 0.0
    priority: int = 1
    status: str = "pending"
    recovery_suggestions: Optional[List[str]] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.recovery_suggestions is None:
            self.recovery_suggestions = []


@dataclass
class ExecutionPlan:
    request_id: str
    original_request: str
    task_type: TaskType
    complexity: ComplexityLevel
    steps: List[TaskStep]
    requires_agents: bool
    estimated_total_time: float
    priority: int
    prompt: str
    context_requirements: Optional[List[str]] = None
    confidence: float = 0.8
    routing_metadata: Optional[Dict[str, Any]] = None
    failure_suggestions: Optional[List[str]] = None

    def __post_init__(self):
        if self.context_requirements is None:
            self.context_requirements = []
        if self.routing_metadata is None:
            self.routing_metadata = {}
        if self.failure_suggestions is None:
            self.failure_suggestions = []


class Planner:

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.request_counter = 0

    def _matches_keywords(self, text: str, keywords: List[str]) -> bool:
        """Match keywords as whole words/phrases (avoids substring false positives)"""
        for kw in keywords:
            if re.search(rf"\b{re.escape(kw)}\b", text):
                return True
        return False

    def _is_system_analysis(self, text: str) -> bool:
        """Detect questions about JARVIS's own system/state (routed to SystemIntelligence)"""
        patterns = [
            r"\bmodules?\b",
            r"\bsystem\s+(status|check|analysis|health|info|overview|monitor|scan)\b",
            r"\bhealth\s*check\b",
            r"check\s+(your|our|the)\s+health",
            r"\bhow\s+(is|are)\s+(your|the|my)\s+(system|modules|agents|gpu|cpu|ram|memory)\b",
            r"\bwhat\s+model\s+(are|do)\b",
            r"\bwhich\s+model\b",
            r"\bmodel\s+are\s+you\s+using\b",
            r"\bgpu\b",
            r"\bwhat('s| is)?\s*(is\s+)?running\b",
            r"\bagents?\s+(active|running|status|enabled)\b",
            r"\bactive\s+agents\b",
            r"\banalyz\w*\s+(the\s+|my\s+|your\s+)?system\b",
            r"\bsystem\s+analysis\b",
            r"\bollama\b",
            r"\byour\s+(status|health|state)\b",
            r"\bstatus\s+report\b",
            r"\bhardware\b",
            r"\b(cpu|ram|memory|disk)\s+(usage|load|status|state)\b",
            r"\bhow\s+are\s+you\s+(running|doing)\b",
        ]
        return any(re.search(p, text) for p in patterns)


    async def create_plan(
        self,
        user_input: str,
        context: List[Dict[str, Any]],
        personality_state: Dict[str, Any]
    ) -> ExecutionPlan:

        self.request_counter += 1

        request_id = (
            f"req_{self.request_counter}_"
            f"{int(asyncio.get_running_loop().time())}"
        )

        self.logger.info(
            f"Creating plan {request_id}: {user_input[:50]}"
        )

        task_type = await self._classify_task_type(
            user_input,
            context
        )

        complexity = await self._assess_complexity(
            user_input,
            task_type,
            context
        )

        # Intent classification and confidence scoring
        intent_label, intent_confidence = await self._classify_intent(user_input, task_type, context)

        requires_agents = await self._requires_multi_agent(
            task_type,
            complexity
        )

        steps = await self._generate_plan_steps(
            user_input,
            task_type,
            complexity,
            context,
            requires_agents
        )

        prompt = await self._create_execution_prompt(
            user_input,
            task_type,
            complexity,
            context,
            personality_state
        )

        estimated_time = sum(
            step.estimated_time for step in steps
        )

        # routing metadata helps downstream components understand why
        routing_metadata = {
            "intent": intent_label,
            "intent_confidence": round(float(intent_confidence), 3),
            "requires_agents": bool(requires_agents),
            "step_count": len(steps),
        }

        failure_suggestions = await self._suggest_failure_recovery(user_input, task_type, complexity, steps)

        plan = ExecutionPlan(
            request_id=request_id,
            original_request=user_input,
            task_type=task_type,
            complexity=complexity,
            steps=steps,
            requires_agents=requires_agents,
            estimated_total_time=estimated_time,
            priority=1,
            prompt=prompt,
            context_requirements=[
                "recent_conversation",
                "user_preferences"
            ],
            confidence=float(intent_confidence),
            routing_metadata=routing_metadata,
            failure_suggestions=failure_suggestions,
        )

        self.logger.info(
            f"Plan created: {task_type.value} | "
            f"{complexity.value} | "
            f"{len(steps)} steps | intent={intent_label}({intent_confidence:.2f})"
        )

        # Emit planner_state event to websocket manager (best-effort, non-blocking)
        try:
            from api.websocket import manager  # type: ignore
            event = {
                "type": "planner_state",
                "data": {
                    "plan_id": plan.request_id,
                    "intent": routing_metadata.get("intent"),
                    "confidence": float(plan.confidence or 0.0),
                    "task_type": plan.task_type.value if plan.task_type else None,
                    "steps": [
                        {"id": s.id, "description": s.description, "agent_type": s.agent_type, "status": s.status}
                        for s in plan.steps
                    ]
                }
            }
            # fire-and-forget
            asyncio.create_task(manager.broadcast(event))
        except Exception:
            # Do not fail planning if websocket not available
            pass

        return plan


    async def _classify_task_type(
        self,
        user_input: str,
        context: List[Dict[str, Any]]
    ) -> TaskType:

        text = user_input.lower()

        if self._is_system_analysis(text):
            return TaskType.SYSTEM_ANALYSIS

        if self._matches_keywords(text, [
            "code",
            "program",
            "script",
            "function",
            "class"
        ]):
            return TaskType.CODE_GENERATION

        if self._matches_keywords(text, [
            "debug",
            "error",
            "bug",
            "fix"
        ]):
            return TaskType.DEBUGGING

        if self._matches_keywords(text, [
            "search",
            "research",
            "explain",
            "investigate",
            "compare",
            "analyze"
        ]):
            return TaskType.RESEARCH

        if self._matches_keywords(text, [
            "file",
            "folder",
            "directory"
        ]):
            return TaskType.FILE_OPERATION

        if self._matches_keywords(text, [
            "run",
            "execute",
            "terminal",
            "command"
        ]):
            return TaskType.SYSTEM_COMMAND

        if self._matches_keywords(text, [
            "open",
            "close",
            "launch",
            "start",
            "stop",
            "screenshot",
            "window",
            "focus",
            "clipboard",
            "click",
            "mouse",
            "keyboard",
            "type",
            "apri",
            "chiudi",
            "avvia",
            "lancia",
            "schermata",
            "finestra",
            "stato del pc",
            "organize",
            "organizza"
        ]):
            return TaskType.AUTOMATION

        if self._matches_keywords(text, [
            "plan",
            "architecture",
            "design"
        ]):
            return TaskType.PLANNING

        return TaskType.GENERAL_QUESTION


    async def _assess_complexity(
        self,
        user_input: str,
        task_type: TaskType,
        context: List[Dict[str, Any]]
    ) -> ComplexityLevel:

        text = user_input.lower()
        words = len(user_input.split())

        if words > 50 or self._matches_keywords(text, [
            "enterprise",
            "architecture",
            "scalable",
            "distributed",
            "advanced"
        ]):
            return ComplexityLevel.EXPERT

        if words > 20 or self._matches_keywords(text, [
            "application",
            "website",
            "api",
            "database",
            "authentication"
        ]):
            return ComplexityLevel.COMPLEX

        if words > 10 or self._matches_keywords(text, [
            "function",
            "class",
            "object",
            "method"
        ]):
            return ComplexityLevel.MODERATE

        return ComplexityLevel.SIMPLE


    async def _classify_intent(
        self,
        user_input: str,
        task_type: TaskType,
        context: List[Dict[str, Any]]
    ) -> (str, float):
        """Lightweight intent classifier returning a label and confidence.

        This is intentionally heuristic to avoid extra dependencies. It returns
        a simple intent label (e.g., 'simple_question', 'coding_task',
        'research_task', 'automation', 'system_operation', 'multi_step') and a
        confidence score between 0.0 and 1.0. More advanced classifiers can be
        plugged in later.
        """
        text = user_input.lower()
        # Base confidence derived from length and explicit keywords
        words = len(user_input.split())
        confidence = 0.75

        if words < 8 and task_type == TaskType.GENERAL_QUESTION:
            confidence = 0.92
            return "simple_question", confidence

        if task_type == TaskType.CODE_GENERATION:
            confidence = 0.9 if self._matches_keywords(text, ["code", "implement", "function"]) else 0.75
            return "coding_task", confidence

        if task_type == TaskType.RESEARCH:
            confidence = 0.88 if self._matches_keywords(text, ["research", "compare", "investigate"]) else 0.7
            return "research_task", confidence

        if task_type in (TaskType.AUTOMATION, TaskType.SYSTEM_COMMAND, TaskType.FILE_OPERATION):
            confidence = 0.9
            return "automation", confidence

        if task_type == TaskType.PLANNING or (words > 30 and self._matches_keywords(text, ["plan", "architecture", "roadmap"])):
            confidence = 0.85
            return "multi_step", confidence

        if task_type == TaskType.SYSTEM_ANALYSIS:
            return "system_operation", 0.95

        # Fallback
        return "general_assistant", round(min(0.9, confidence), 3)


    async def _suggest_failure_recovery(
        self,
        user_input: str,
        task_type: TaskType,
        complexity: ComplexityLevel,
        steps: List[TaskStep]
    ) -> List[str]:
        """Generate brief recovery suggestions if tasks fail. These are human readable
        hints presented to the user or operator to recover from typical failures.
        """
        suggestions: List[str] = []

        if task_type == TaskType.CODE_GENERATION:
            suggestions.append("If code generation fails, ask for a minimal reproducible example or smaller scope.")
            suggestions.append("Run unit tests locally and provide failing stack traces for debugging.")

        if task_type == TaskType.RESEARCH:
            suggestions.append("If results are incomplete, request additional sources or a narrower query.")

        if task_type in (TaskType.AUTOMATION, TaskType.SYSTEM_COMMAND):
            suggestions.append("Verify the target system permissions and run with --dry-run for safety.")

        if any(s.priority > 2 for s in steps):
            suggestions.append("Prioritize critical steps and run them sequentially to isolate failures.")

        if not suggestions:
            suggestions.append("If the task fails, try simplifying the request or request a step-by-step plan.")

        return suggestions


    async def _requires_multi_agent(
        self,
        task_type: TaskType,
        complexity: ComplexityLevel
    ) -> bool:

        multi_agent_tasks = {
            TaskType.PLANNING,
            TaskType.RESEARCH,
            TaskType.ANALYSIS,
            TaskType.CODE_GENERATION
        }

        return (
            complexity in [
                ComplexityLevel.COMPLEX,
                ComplexityLevel.EXPERT
            ]
            or task_type in multi_agent_tasks
        )


    async def _generate_plan_steps(
        self,
        user_input: str,
        task_type: TaskType,
        complexity: ComplexityLevel,
        context: List[Dict[str, Any]],
        requires_agents: bool
    ) -> List[TaskStep]:

        steps = []

        if requires_agents:

            if task_type == TaskType.PLANNING:
                steps.extend([
                    TaskStep(
                        "research",
                        "Research requirements and solutions",
                        "research_agent",
                        estimated_time=5
                    ),
                    TaskStep(
                        "design",
                        "Create architecture design",
                        "coding_agent",
                        estimated_time=10
                    ),
                    TaskStep(
                        "review",
                        "Review security and quality",
                        "security_agent",
                        estimated_time=5
                    )
                ])

            elif task_type == TaskType.CODE_GENERATION:

                steps.extend([
                    TaskStep(
                        "implement",
                        "Generate implementation",
                        "coding_agent",
                        estimated_time=10
                    ),
                    TaskStep(
                        "review",
                        "Review generated code",
                        "security_agent",
                        estimated_time=5
                    )
                ])

            elif task_type == TaskType.RESEARCH:

                steps.extend([
                    TaskStep(
                        "research",
                        "Research and summarize the topic",
                        "research_agent",
                        estimated_time=10
                    )
                ])

            elif task_type in (
                TaskType.AUTOMATION,
                TaskType.SYSTEM_COMMAND,
                TaskType.FILE_OPERATION,
            ):

                steps.extend([
                    TaskStep(
                        "system_execute",
                        f"Execute {task_type.value} via the System Agent",
                        "system_agent",
                        estimated_time=(
                            3.0
                            if complexity == ComplexityLevel.SIMPLE
                            else 8.0
                        )
                    )
                ])

            else:
                # No specialist agents apply - the brain's own generation
                # (via the plan prompt) handles the request directly.
                pass

        else:

            if task_type in (
                TaskType.AUTOMATION,
                TaskType.SYSTEM_COMMAND,
                TaskType.FILE_OPERATION,
            ):

                steps.append(
                    TaskStep(
                        id="system_execute",
                        description=(
                            f"Execute {task_type.value} via the System Agent"
                        ),
                        agent_type="system_agent",
                        estimated_time=(
                            2.0
                            if complexity == ComplexityLevel.SIMPLE
                            else 5.0
                        )
                    )
                )

            else:

                steps.append(
                    TaskStep(
                        id="process",
                        description=(
                            f"Process {task_type.value} request"
                        ),
                        agent_type="main_agent",
                        estimated_time=(
                            2.0
                            if complexity == ComplexityLevel.SIMPLE
                            else 5.0
                        )
                    )
                )

        return steps


    async def _create_execution_prompt(
        self,
        user_input: str,
        task_type: TaskType,
        complexity: ComplexityLevel,
        context: List[Dict[str, Any]],
        personality_state: Dict[str, Any]
    ) -> str:

        context_text = ""

        if context:
            messages = []

            for msg in context[-5:]:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")

                messages.append(
                    f"{role}: {content[:200]}"
                )

            context_text = (
                "\nRecent conversation:\n"
                + "\n".join(messages)
            )


        prompts = {
            TaskType.GENERAL_QUESTION:
                "Answer clearly and accurately:",

            TaskType.CODE_GENERATION:
                "Write production-ready code:",

            TaskType.CODE_REVIEW:
                "Review the code and suggest improvements:",

            TaskType.DEBUGGING:
                "Debug and fix the problem:",

            TaskType.ARCHITECTURE_DESIGN:
                "Design a scalable, maintainable architecture:",

            TaskType.REFACTORING:
                "Refactor the code safely while preserving functionality:",

            TaskType.DOCUMENTATION:
                "Write clear, comprehensive documentation:",

            TaskType.RESEARCH:
                "Research and explain the topic:",

            TaskType.FILE_OPERATION:
                "Handle the requested file operation safely:",

            TaskType.SYSTEM_COMMAND:
                "Execute the system operation safely:",

            TaskType.AUTOMATION:
                "Create an automation solution:",

            TaskType.CREATIVE_WRITING:
                "Create the requested content:",

            TaskType.ANALYSIS:
                "Analyze the information:",

            TaskType.PLANNING:
                "Create a detailed plan:",

            TaskType.SYSTEM_ANALYSIS:
                "Analyze the system using the provided real data:"
        }


        base = prompts.get(
            task_type,
            "Answer the request:"
        )


        return f"""
{base}

Task complexity:
{complexity.value}

User request:
{user_input}

{context_text}

Provide a helpful and complete response.
If code is required, make it clean, secure and production-ready.
""".strip()