"""
JARVIS AI Operating System - Coding Agent
Specialized agent for software development tasks
"""

from __future__ import annotations

import asyncio
import logging
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from datetime import datetime
import re

from core.personality import Personality
from core.model_router import ModelRouter
from core.planner import TaskType
from memory.memory_manager import MemoryManager

if TYPE_CHECKING:
    from core.brain import JARVIS_Brain

logger = logging.getLogger(__name__)


class CodingAgent:
    """
    Coding Agent - Specialized software engineering agent
    Handles code generation, review, debugging, and architecture tasks
    """

    def __init__(self, brain: JARVIS_Brain):
        self.brain = brain
        self.logger = logging.getLogger(__name__)
        self.personality = Personality()
        self.memory_manager = MemoryManager()
        self.model_router = ModelRouter()
        self.is_initialized = False
        self.last_error: Optional[str] = None

        # Agent metadata
        self.agent_id = "coding_agent"
        self.agent_name = "CodeMaster"
        self.agent_type = "specialist"
        self.specializations = [
            "code_generation",
            "code_review",
            "debugging",
            "architecture_design",
            "algorithm_implementation",
            "api_development",
            "database_design",
            "refactoring",
            "performance_optimization",
            "technical_documentation"
        ]

        # Supported languages
        self.supported_languages = [
            "python", "javascript", "typescript", "java", "cpp", "c",
            "csharp", "go", "rust", "php", "ruby", "swift", "kotlin",
            "html", "css", "sql", "bash", "powershell"
        ]

    async def initialize(self):
        """Initialize the coding agent"""
        try:
            self.logger.info("Initializing Coding Agent...")
            await self.personality.initialize()
            await self.memory_manager.initialize()
            await self.model_router.initialize()
            self.is_initialized = True
            self.logger.info("Coding Agent initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Coding Agent: {e}")
            raise

    async def process_request(
        self,
        request: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a coding-related request

        Args:
            request: The coding request from user
            context: Additional context (files, existing code, etc.)

        Returns:
            Dictionary containing response and metadata
        """
        if not self.is_initialized:
            await self.initialize()

        try:
            self.logger.info(f"Coding Agent processing request: {request[:100]}...")

            # Analyze the request to determine specific task type
            task_type = await self._classify_coding_task(request)
            complexity = await self._assess_complexity(request, context)

            # Store request in memory
            await self.memory_manager.store_conversation(
                role="user",
                content=request,
                modality="text",
                timestamp=datetime.now(),
                metadata={"agent": self.agent_id, "task_type": task_type.value}
            )

            # Get relevant context from memory
            memory_context = await self.memory_manager.get_recent_context(limit=10)
            if context:
                memory_context.append(context)

            # Route to appropriate model for coding tasks
            model_selection = await self.model_router.select_model(
                task_type=task_type,
                complexity=complexity,
                context=memory_context
            )

            # Generate specialized prompt for coding task
            coding_prompt = await self._create_coding_prompt(
                request, task_type, context, memory_context
            )

            # Generate response using the selected model
            raw_response = await self.model_router.generate(
                prompt=coding_prompt,
                model=model_selection.model_name,
                context=memory_context,
                temperature=model_selection.temperature,
                max_tokens=model_selection.max_tokens
            )

            # Post-process the response for code quality
            processed_response = await self._post_process_code_response(
                raw_response, request, task_type
            )

            # Apply personality
            personalized_response = await self.personality.apply_personality(
                processed_response, memory_context, request
            )

            # Store response
            await self.memory_manager.store_conversation(
                role="assistant",
                content=personalized_response,
                modality="text",
                timestamp=datetime.now(),
                metadata={
                    "agent": self.agent_id,
                    "task_type": task_type.value,
                    "model_used": model_selection.model_name
                }
            )

            return {
                "response": personalized_response,
                "agent": self.agent_id,
                "agent_name": self.agent_name,
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "task_type": task_type.value,
                    "complexity": complexity,
                    "model_used": model_selection.model_name,
                    "reason": model_selection.reason,
                    "code_extracted": self._extract_code_blocks(personalized_response)
                }
            }

        except Exception as e:
            self.last_error = str(e)
            self.logger.error(f"Error in Coding Agent processing: {e}", exc_info=True)
            error_response = await self.personality.handle_error(str(e))
            return {
                "response": error_response,
                "agent": self.agent_id,
                "timestamp": datetime.now().isoformat(),
                "error": True,
                "metadata": {
                    "agent": self.agent_id,
                    "error": str(e)
                }
            }

    async def _classify_coding_task(self, request: str) -> TaskType:
        """Classify the type of coding task"""
        request_lower = request.lower()

        # Define keywords for each task type
        task_keywords = {
            TaskType.CODE_GENERATION: [
                "write", "create", "build", "make", "develop", "implement",
                "code", "program", "script", "function", "class", "method"
            ],
            TaskType.CODE_REVIEW: [
                "review", "check", "review", "audit", "inspect", "evaluate",
                "quality", "best practices", "style", "lint"
            ],
            TaskType.DEBUGGING: [
                "debug", "fix", "error", "bug", "issue", "problem", "broken",
                "not working", "fail", "exception", "crash"
            ],
            TaskType.ARCHITECTURE_DESIGN: [
                "architecture", "design", "structure", "system", "components",
                "modules", "microservices", "database design", "api design"
            ],
            TaskType.REFACTORING: [
                "refactor", "restructure", "reorganize", "clean up", "improve",
                "optimize", "clean", "streamline"
            ],
            TaskType.DOCUMENTATION: [
                "document", "comment", "explain", "describe", "readme",
                "documentation", "docstring", "api docs"
            ]
        }

        # Score each task type
        scores = {}
        for task_type, keywords in task_keywords.items():
            score = sum(1 for keyword in keywords if keyword in request_lower)
            scores[task_type] = score

        # Return the highest scoring task type, default to code generation
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        else:
            return TaskType.CODE_GENERATION  # Default

    async def _assess_complexity(self, request: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Assess the complexity of the coding task"""
        request_lower = request.lower()
        indicators = {
            "simple": ["simple", "basic", "small", "quick", "tiny", "minimal"],
            "moderate": ["moderate", "medium", "standard", "normal", "average"],
            "complex": ["complex", "advanced", "complex", "sophisticated", "elaborate"],
            "expert": ["expert", "enterprise", "scalable", "architecture", "distributed", "microservices"]
        }

        # Check for explicit complexity indicators
        for complexity_level, keywords in indicators.items():
            if any(keyword in request_lower for keyword in keywords):
                return complexity_level

        # Implicit complexity based on request length and technical depth
        word_count = len(request.split())
        if word_count < 10:
            return "simple"
        elif word_count < 30:
            return "moderate"
        elif word_count < 60:
            return "complex"
        else:
            return "expert"

    async def _create_coding_prompt(
        self,
        request: str,
        task_type: TaskType,
        context: Optional[Dict[str, Any]],
        memory_context: List[Dict[str, Any]]
    ) -> str:
        """Create a specialized prompt for coding tasks"""
        # Base prompt components
        prompt_parts = []

        # System/context setting
        prompt_parts.append("You are an expert software engineer with deep knowledge of multiple programming languages, frameworks, and best practices.")

        # Task-specific instructions
        task_instructions = {
            TaskType.CODE_GENERATION: "Write clean, production-ready code that follows best practices and includes proper error handling.",
            TaskType.CODE_REVIEW: "Review the provided code for quality, security, performance, and adherence to best practices. Provide specific, actionable feedback.",
            TaskType.DEBUGGING: "Analyze the problem, identify the root cause, and provide a clear solution with explanations.",
            TaskType.ARCHITECTURE_DESIGN: "Design a scalable, maintainable architecture following established patterns and principles.",
            TaskType.REFACTORING: "Refactor the code to improve readability, maintainability, and performance while preserving functionality.",
            TaskType.DOCUMENTATION: "Create clear, comprehensive documentation that explains the code's purpose, usage, and implementation details."
        }

        if task_type in task_instructions:
            prompt_parts.append(task_instructions[task_type])

        # Add context information
        if context:
            if "files" in context:
                prompt_parts.append(f"Working with files: {', '.join(context['files'])}")
            if "language" in context:
                prompt_parts.append(f"Programming language: {context['language']}")
            if "framework" in context:
                prompt_parts.append(f"Framework: {context['framework']}")

        # Add relevant conversation context
        if memory_context:
            recent_topics = []
            for item in memory_context[-3:]:  # Last 3 items
                if item.get("content"):
                    content_preview = item["content"][:100]
                    recent_topics.append(content_preview)
            if recent_topics:
                prompt_parts.append(f"Recent context: {' | '.join(recent_topics)}")

        # Add the actual request
        prompt_parts.append(f"\nUser Request: {request}")

        # Add quality guidelines
        prompt_parts.append("""
Please ensure your response includes:
1. Clear explanation of the approach
2. Well-formatted, readable code (if applicable)
3. Comments explaining complex logic
4. Consideration of edge cases and error handling
5. Adherence to language-specific best practices
6. If suggesting multiple approaches, explain trade-offs

Format your response clearly and professionally.
""")

        return "\n".join(prompt_parts)

    async def _post_process_code_response(
        self,
        response: str,
        original_request: str,
        task_type: TaskType
    ) -> str:
        """Post-process the response to ensure code quality and relevance"""
        # Extract code blocks if present
        code_blocks = self._extract_code_blocks(response)

        # If we have code blocks, we might want to validate or format them
        # For now, we'll just ensure the response is well-structured

        # Add coding agent signature for transparency
        if not response.endswith("--"):
            response += "\n\n--\n*Generated by JARVIS Coding Agent*"

        return response

    def _extract_code_blocks(self, text: str) -> List[Dict[str, str]]:
        """Extract code blocks from text"""
        code_blocks = []

        # Pattern for markdown code blocks
        pattern = r'```(\w+)?\n(.*?)\n```'
        matches = re.findall(pattern, text, re.DOTALL)

        for language, code in matches:
            code_blocks.append({
                "language": language or "text",
                "code": code.strip()
            })

        # Also check for indented code blocks (simple heuristic)
        lines = text.split('\n')
        in_code_block = False
        current_block = []
        current_language = None

        for line in lines:
            if line.startswith('    ') or line.startswith('\t'):
                if not in_code_block:
                    in_code_block = True
                    current_language = "text"  # Assume text if not specified
                current_block.append(line[4:] if line.startswith('    ') else line[1:])
            else:
                if in_code_block and current_block:
                    code_blocks.append({
                        "language": current_language,
                        "code": '\n'.join(current_block).strip()
                    })
                    current_block = []
                    in_code_block = False

        # Handle trailing code block
        if in_code_block and current_block:
            code_blocks.append({
                "language": current_language,
                "code": '\n'.join(current_block).strip()
            })

        return code_blocks

    async def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "agent_type": self.agent_type,
            "is_initialized": self.is_initialized,
            "health_state": "healthy" if self.is_initialized and not self.last_error else ("degraded" if self.last_error else "standby"),
            "last_error": self.last_error,
            "specializations": self.specializations,
            "supported_languages": self.supported_languages,
            "last_activity": datetime.now().isoformat()
        }

    async def shutdown(self):
        """Shutdown the agent"""
        self.logger.info("Shutting down Coding Agent")
        self.is_initialized = False