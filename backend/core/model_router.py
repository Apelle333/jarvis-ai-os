"""
JARVIS Model Router
Single source of truth for Ollama model selection and generation.
Routes tasks to the most appropriate AI model based on task type and complexity.

The ``TaskType`` and ``ComplexityLevel`` enums live in ``core.planner``;
this module must be the only place that defines ``ModelRouter`` and
``ModelSelection`` (the former ``models.model_router`` has been merged here).
"""
import asyncio
import logging
from datetime import datetime
import ollama

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .settings import settings
from .planner import TaskType, ComplexityLevel

logger = logging.getLogger(__name__)


@dataclass
class ModelSelection:
    """Result of model selection process.

    ``model`` is the canonical attribute; ``model_name`` is provided as a
    compatibility alias used by several agents.
    """
    model: str
    confidence: float = 0.8
    reason: str = ""
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 0.9

    @property
    def model_name(self) -> str:
        return self.model


class ModelRouter:
    """Routes tasks to the most appropriate AI model."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.available_models: Dict[str, bool] = {}
        self.model_capabilities: Dict[str, List[TaskType]] = {}
        self.runtime_metrics: Dict[str, Any] = {
            "availability_check_ms": 0.0,
            "selection_ms": 0.0,
            "generation_ms": 0.0,
            "generation_errors": 0,
            "selection_count": 0,
        }

        self._initialize_model_capabilities()

    def _initialize_model_capabilities(self):
        """Build the model -> task-type capability map from configuration.

        Models can fill multiple roles (e.g. coder == reasoning), so the
        capability list for each model name is accumulated across roles.
        """
        default_model = settings.default_model or "gemma4:12b"
        coder_model = settings.coder_model or "qwen3.6:27b-q4_K_M"
        reasoning_model = settings.reasoning_model or "qwen3.6:27b-q4_K_M"

        self.models = {
            "default": default_model,
            "coder": coder_model,
            "reasoning": reasoning_model,
        }

        role_capabilities = [
            (default_model, [
                TaskType.GENERAL_QUESTION,
                TaskType.CREATIVE_WRITING,
                TaskType.RESEARCH,
                TaskType.ANALYSIS,
                TaskType.FILE_OPERATION,
                TaskType.SYSTEM_COMMAND,
                TaskType.AUTOMATION,
                TaskType.SYSTEM_ANALYSIS,
            ]),
            (coder_model, [
                TaskType.CODE_GENERATION,
                TaskType.CODE_REVIEW,
                TaskType.DEBUGGING,
                TaskType.ARCHITECTURE_DESIGN,
                TaskType.REFACTORING,
                TaskType.PLANNING,
                TaskType.ANALYSIS,
            ]),
            (reasoning_model, [
                TaskType.PLANNING,
                TaskType.RESEARCH,
                TaskType.ANALYSIS,
                TaskType.CODE_GENERATION,
                TaskType.DEBUGGING,
                TaskType.ARCHITECTURE_DESIGN,
                TaskType.REFACTORING,
                TaskType.SYSTEM_ANALYSIS,
            ]),
        ]

        merged: Dict[str, List[TaskType]] = {}
        for model_name, task_types in role_capabilities:
            merged.setdefault(model_name, [])
            for task_type in task_types:
                if task_type not in merged[model_name]:
                    merged[model_name].append(task_type)
        self.model_capabilities = merged

    async def initialize(self):
        """Initialize the model router by checking available models."""
        await self._check_available_models()
        self.logger.info("Model Router initialized")

    async def _check_available_models(self):
        """Check which configured models are available in Ollama."""
        availability_start = datetime.now()
        try:
            models_info = ollama.list()
            available_model_names = [
                model["model"] for model in models_info["models"]
            ]

            for model_name in self.model_capabilities.keys():
                # Tolerate version-suffix drift between config and Ollama.
                is_available = any(
                    model_name in available_model
                    or available_model.startswith(model_name.split(":")[0])
                    for available_model in available_model_names
                )
                self.available_models[model_name] = is_available

                if is_available:
                    self.logger.info(f"Model {model_name} is available")
                else:
                    self.logger.warning(f"Model {model_name} is not available")

        except Exception as e:
            self.logger.error(f"Error checking available models: {e}")
            # Fallback to assuming models are available so routing can proceed.
            for model_name in self.model_capabilities.keys():
                self.available_models[model_name] = True
        finally:
            self.runtime_metrics["availability_check_ms"] = (
                datetime.now() - availability_start
            ).total_seconds() * 1000.0

    async def is_model_available(self, model_name: str) -> bool:
        """Check if a specific model is available (cached, then live)."""
        if model_name in self.available_models:
            return self.available_models[model_name]

        availability_start = datetime.now()
        try:
            models_info = ollama.list()
            available = [
                model["model"] for model in models_info["models"]
            ]
            result = model_name in available
            self.available_models[model_name] = result
            return result
        except Exception:
            return False
        finally:
            self.runtime_metrics["availability_check_ms"] = (
                datetime.now() - availability_start
            ).total_seconds() * 1000.0

    @staticmethod
    def _normalize_complexity(complexity: Any) -> str:
        """Coerce a ComplexityLevel enum or string into a plain string."""
        if isinstance(complexity, ComplexityLevel):
            return complexity.value
        return str(complexity)

    async def select_model(
        self,
        task_type: TaskType,
        complexity: Any,
        context: Optional[List[Dict[str, Any]]] = None,
    ) -> ModelSelection:
        """
        Select the best model for the given task.

        Args:
            task_type: Type of task to perform.
            complexity: Complexity level (``ComplexityLevel`` or ``str``).
            context: Additional context for decision making.

        Returns:
            ModelSelection: Selected model and parameters.
        """
        complexity = self._normalize_complexity(complexity)

        # Get candidate models for this task type.
        candidate_models = []
        for model, capabilities in self.model_capabilities.items():
            if task_type in capabilities and self.available_models.get(model, False):
                candidate_models.append(model)

        # Fall back to general-purpose models if none are specialized.
        if not candidate_models:
            candidate_models = [
                model for model, available in self.available_models.items()
                if available
                and TaskType.GENERAL_QUESTION in self.model_capabilities.get(model, [])
            ]

        # Last resort: any available model.
        if not candidate_models:
            candidate_models = [
                model for model, available in self.available_models.items()
                if available
            ]

        # If nothing is known to be available, prefer the default model.
        if not candidate_models:
            candidate_models = [self.models["default"]]

        selection_start = datetime.now()
        selected_model = await self._select_best_model(
            candidate_models, task_type, complexity, context
        )
        self.runtime_metrics["selection_ms"] = (
            datetime.now() - selection_start
        ).total_seconds() * 1000.0
        self.runtime_metrics["selection_count"] += 1

        temperature, max_tokens = self._get_model_parameters(
            task_type, complexity
        )

        reason = self._generate_selection_reason(
            selected_model, task_type, complexity, candidate_models
        )

        return ModelSelection(
            model=selected_model,
            confidence=0.8,
            reason=reason,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=0.9,
        )

    async def _select_best_model(
        self,
        candidates: List[str],
        task_type: TaskType,
        complexity: str,
        context: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Score and select the best model from a list of candidates."""
        scores: Dict[str, float] = {}

        for model in candidates:
            score = 0.0

            # Prefer models that explicitly support this task type.
            if task_type in self.model_capabilities.get(model, []):
                score += 3.0

            # Adjust for complexity.
            if complexity == "expert" and "27b" in model:
                score += 2.0  # Prefer larger models for expert tasks.
            elif complexity == "simple" and "12b" in model:
                score += 1.0  # Prefer smaller models for simple tasks.

            # Task-specific preferences.
            if task_type == TaskType.CODE_GENERATION and "qwen" in model.lower():
                score += 2.0
            elif task_type == TaskType.GENERAL_QUESTION and "gemma" in model.lower():
                score += 2.0
            elif (
                task_type in [TaskType.PLANNING, TaskType.RESEARCH]
                and "27b" in model
                and complexity == "expert"
            ):
                score += 2.0

            scores[model] = score

        if scores:
            best_model = max(scores, key=scores.get)
            self.logger.debug(f"Model scores: {scores}, selected: {best_model}")
            return best_model

        return candidates[0] if candidates else self.models["default"]

    def _get_model_parameters(
        self, task_type: TaskType, complexity: str
    ) -> tuple:
        """Get optimal temperature and max_tokens for the task."""
        temperature = 0.7
        max_tokens = 2048

        if task_type == TaskType.CODE_GENERATION:
            temperature = 0.3
            max_tokens = 4096
        elif task_type == TaskType.CODE_REVIEW:
            temperature = 0.2
            max_tokens = 2048
        elif task_type == TaskType.REFACTORING:
            temperature = 0.3
            max_tokens = 3072
        elif task_type == TaskType.ARCHITECTURE_DESIGN:
            temperature = 0.5
            max_tokens = 4096
        elif task_type == TaskType.DOCUMENTATION:
            temperature = 0.5
            max_tokens = 4096
        elif task_type == TaskType.CREATIVE_WRITING:
            temperature = 0.8
            max_tokens = 3072
        elif task_type == TaskType.RESEARCH:
            temperature = 0.5
            max_tokens = 3072
        elif task_type == TaskType.ANALYSIS:
            temperature = 0.4
            max_tokens = 3072

        if complexity == "simple":
            max_tokens = min(max_tokens, 1024)
        elif complexity == "expert":
            max_tokens = min(max_tokens * 2, 8192)

        return temperature, max_tokens

    def _generate_selection_reason(
        self,
        selected_model: str,
        task_type: TaskType,
        complexity: str,
        candidates: List[str],
    ) -> str:
        """Generate a human-readable reason for the model selection."""
        reasons = []

        if task_type in self.model_capabilities.get(selected_model, []):
            reasons.append(
                f"{selected_model} is well-suited for {task_type.value}"
            )

        if complexity == "expert" and "27b" in selected_model:
            reasons.append("Selected larger 27B model for expert-level complexity")
        elif complexity == "simple" and "12b" in selected_model:
            reasons.append("Selected efficient 12B model for simple task")

        if not reasons:
            reasons.append(f"Selected {selected_model} as best available option")

        return "; ".join(reasons)

    async def generate(
        self,
        prompt: str,
        model: str,
        context: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """
        Generate text using the specified model.

        Args:
            prompt: The prompt to send to the model.
            model: Model name to use.
            context: Conversation context.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Returns:
            Generated text response.
        """
        messages: List[Dict[str, str]] = []

        if context:
            for ctx_item in context[-5:]:
                role = ctx_item.get("role")
                content = ctx_item.get("content")
                if role and content:
                    messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": prompt})

        generation_start = datetime.now()
        self.runtime_metrics["generation_requests"] = (
            self.runtime_metrics.get("generation_requests", 0) + 1
        )
        try:
            response = await asyncio.to_thread(
                ollama.chat,
                model=model,
                messages=messages,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "top_p": 0.9,
                },
            )
            return response["message"]["content"]
        except Exception as e:
            self.runtime_metrics["generation_errors"] += 1
            self.logger.error(
                "Model generation failed: %s | model=%s",
                e,
                model,
                exc_info=True,
            )
            raise
        finally:
            self.runtime_metrics["generation_ms"] = (
                datetime.now() - generation_start
            ).total_seconds() * 1000.0

    async def pull_model(self, model_name: str) -> bool:
        """Pull/download a model if not available.

        Returns:
            bool: Success status.
        """
        try:
            self.logger.info(f"Pulling model {model_name}...")
            await asyncio.to_thread(ollama.pull, model_name)
            self.available_models[model_name] = True
            self.logger.info(f"Successfully pulled model {model_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to pull model {model_name}: {e}")
            return False

    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get detailed info about models available in Ollama."""
        try:
            response = ollama.list()
            models = getattr(response, "models", response)
            if hasattr(models, "model_dump"):
                models = models.model_dump()

            if isinstance(models, dict):
                return list(models.get("models", []))

            return [
                {
                    "model": getattr(m, "model", None),
                    "modified_at": str(getattr(m, "modified_at", "")),
                    "digest": getattr(m, "digest", None),
                    "size": getattr(m, "size", 0),
                }
                for m in models
            ]
        except Exception:
            return []

    async def cleanup(self):
        """Cleanup resources. Models stay cached in Ollama."""
        self.logger.info("Model Router cleanup completed")
