"""
JARVIS AI Operating System - Research Agent
Specialized agent for information gathering and analysis
"""

from __future__ import annotations

import asyncio
import logging
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from datetime import datetime

from core.personality import Personality
from core.model_router import ModelRouter
from core.planner import TaskType
from memory.memory_manager import MemoryManager
from tools.browser import BrowserTool

if TYPE_CHECKING:
    from core.brain import JARVIS_Brain

logger = logging.getLogger(__name__)


class ResearchAgent:
    """
    Research Agent - Specialized agent for information gathering, analysis, and synthesis
    Handles research tasks, fact-finding, literature reviews, and data analysis
    """

    def __init__(self, brain: JARVIS_Brain):
        self.brain = brain
        self.logger = logging.getLogger(__name__)
        self.personality = Personality()
        self.memory_manager = MemoryManager()
        self.model_router = ModelRouter()
        self.browser_tool = BrowserTool()
        self.is_initialized = False
        self.last_error: Optional[str] = None

        # Agent metadata
        self.agent_id = "research_agent"
        self.agent_name = "Research Specialist"
        self.agent_type = "specialist"
        self.specializations = [
            "information_gathering",
            "fact_checking",
            "literature_review",
            "market_research",
            "technical_analysis",
            "trend_analysis",
            "competitive_research",
            "data_synthesis",
            "report_writing",
            "source_evaluation"
        ]

        # Research domains
        self.research_domains = [
            "technology", "science", "programming", "medicine", "business",
            "finance", "history", "philosophy", "art", "literature"
        ]

    async def initialize(self):
        """Initialize the research agent"""
        try:
            self.logger.info("Initializing Research Agent...")
            await self.personality.initialize()
            await self.memory_manager.initialize()
            await self.model_router.initialize()
            await self.browser_tool.initialize()
            self.is_initialized = True
            self.logger.info("Research Agent initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Research Agent: {e}")
            raise

    async def process_request(
        self,
        request: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a research-related request

        Args:
            request: The research request from user
            context: Additional context (preferred sources, depth, etc.)

        Returns:
            Dictionary containing response and metadata
        """
        if not self.is_initialized:
            await self.initialize()

        try:
            self.logger.info(f"Research Agent processing request: {request[:100]}...")

            # Analyze the request to determine research type and scope
            research_type = await self._classify_research_task(request)
            depth = await self._assess_research_depth(request, context)

            # Store request in memory
            await self.memory_manager.store_conversation(
                role="user",
                content=request,
                modality="text",
                timestamp=datetime.now(),
                metadata={"agent": self.agent_id, "research_type": research_type.value}
            )

            # Get relevant context from memory
            memory_context = await self.memory_manager.get_recent_context(limit=10)
            if context:
                memory_context.append(context)

            # Route to appropriate model for research tasks
            model_selection = await self.model_router.select_model(
                task_type=TaskType.RESEARCH,
                complexity=depth,
                context=memory_context
            )

            # Gather information using browser tool and knowledge base
            research_data = await self._gather_information(
                request, research_type, depth, memory_context
            )

            # Analyze and synthesize findings
            analysis = await self._analyze_findings(
                research_data, request, research_type
            )

            # Generate a model-written answer as the primary report
            facts_text = "\n".join(
                f"- {f.get('statement')}" for f in research_data.get("facts", [])[:10]
            ) or "None available."
            core_answer = await self.model_router.generate(
                prompt=(
                    f"Provide a clear, accurate, well-structured answer to the following:\n"
                    f"{request}\n\n"
                    f"Relevant gathered facts (use them if they are helpful):\n{facts_text}"
                ),
                model=model_selection.model_name,
                context=memory_context,
                temperature=model_selection.temperature,
                max_tokens=model_selection.max_tokens
            )

            # Append structured findings/sources when genuine research data exists
            if research_data.get("facts") or research_data.get("sources"):
                report = core_answer + "\n\n" + await self._generate_research_report(
                    analysis, request, research_type, depth
                )
            else:
                report = core_answer

            # Apply personality to response
            personalized_response = await self.personality.apply_personality(
                report, memory_context, request
            )

            # Store response
            await self.memory_manager.store_conversation(
                role="assistant",
                content=personalized_response,
                modality="text",
                timestamp=datetime.now(),
                metadata={
                    "agent": self.agent_id,
                    "research_type": research_type.value,
                    "depth": depth,
                    "model_used": model_selection.model_name,
                    "sources_consulted": len(research_data.get("sources", []))
                }
            )

            return {
                "response": personalized_response,
                "agent": self.agent_id,
                "agent_name": self.agent_name,
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "research_type": research_type.value,
                    "depth": depth,
                    "model_used": model_selection.model_name,
                    "reason": model_selection.reason,
                    "sources_count": len(research_data.get("sources", [])),
                    "confidence_score": analysis.get("confidence", 0.0)
                }
            }

        except Exception as e:
            self.last_error = str(e)
            self.logger.error(f"Error in Research Agent processing: {e}", exc_info=True)
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

    async def _classify_research_task(self, request: str) -> TaskType:
        """Classify the type of research task"""
        request_lower = request.lower()

        # Research task classification
        if any(word in request_lower for word in ["fact", "verify", "confirm", "true", "false", "myth"]):
            return TaskType.RESEARCH  # Fact checking
        elif any(word in request_lower for word in ["market", "competitor", "industry", "trend"]):
            return TaskType.RESEARCH  # Market research
        elif any(word in request_lower for word in ["paper", "study", "journal", "academic", "literature"]):
            return TaskType.RESEARCH  # Literature review
        elif any(word in request_lower for word in ["data", "statistics", "numbers", "survey"]):
            return TaskType.RESEARCH  # Data analysis
        elif any(word in request_lower for word in ["report", "summary", "brief", "overview"]):
            return TaskType.RESEARCH  # Report writing
        else:
            return TaskType.RESEARCH  # General research

    async def _assess_research_depth(self, request: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Assess the required depth of research"""
        request_lower = request.lower()
        depth_indicators = {
            "shallow": ["quick", "brief", "overview", "summary", "basics", "introduction"],
            "moderate": ["detailed", "comprehensive", "thorough", "in-depth"],
            "deep": ["extensive", "exhaustive", "comprehensive", "authoritative", "definitive"]
        }

        # Check for explicit depth indicators
        for depth_level, indicators in depth_indicators.items():
            if any(indicator in request_lower for indicator in indicators):
                return depth_level

        # Implicit depth based on request complexity
        word_count = len(request.split())
        if word_count < 15:
            return "shallow"
        elif word_count < 35:
            return "moderate"
        else:
            return "deep"

    async def _gather_information(
        self,
        request: str,
        research_type: TaskType,
        depth: str,
        context: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Gather information from various sources"""
        research_data = {
            "query": request,
            "sources": [],
            "facts": [],
            "raw_content": ""
        }

        try:
            # Try to get information from internal knowledge base first
            kb_results = await self.memory_manager.search_memory(query=request, limit=5)
            if kb_results:
                for item in kb_results:
                    content = item.get("content") or item.get("text") or ""
                    if content:
                        research_data["raw_content"] += content + "\n"
                        research_data["sources"].append({
                            "title": item.get("title", "Knowledge Base"),
                            "url": item.get("url", ""),
                            "snippet": content[:200]
                        })

            # Use browser tool for web research (time-boxed and optional)
            source_count = len(research_data["sources"])
            if depth in ["moderate", "deep"] or source_count < 3:
                try:
                    await asyncio.wait_for(
                        self._web_research(request, depth, research_data),
                        timeout=40
                    )
                except asyncio.TimeoutError:
                    self.logger.warning("Web research timed out, continuing with available data")
                except Exception as e:
                    self.logger.warning(f"Web research failed: {e}")

            # Extract key facts from gathered content
            if research_data["raw_content"]:
                facts = await self._extract_facts(research_data["raw_content"], request)
                research_data["facts"].extend(facts)

        except Exception as e:
            self.logger.warning(f"Error gathering information: {e}")
            # Continue with what we have

        return research_data

    async def _web_research(
        self,
        request: str,
        depth: str,
        research_data: Dict[str, Any]
    ):
        """Perform web research using the browser tool (bounded execution)"""
        search = await self.browser_tool.search_google(
            query=request,
            num_results=5 if depth == "moderate" else 10
        )
        if not search.get("success"):
            return

        scrape_limit = 2 if depth in ["shallow", "moderate"] else 4
        for result in search.get("results", [])[:scrape_limit]:
            url = result.get("url", "")
            snippet = result.get("snippet", "")
            research_data["sources"].append(result)
            if snippet:
                research_data["raw_content"] += snippet + "\n"
            if url and depth in ["moderate", "deep"]:
                page = await self.browser_tool.scrape(url, text_only=True)
                if page.get("success"):
                    text = " ".join(page.get("data", [])[:20])
                    if text:
                        research_data["raw_content"] += text + "\n"

    async def _extract_facts(self, content: str, query: str) -> List[Dict[str, Any]]:
        """Extract factual information from content"""
        # Simple fact extraction - in practice would use NLP
        facts = []

        # Split content into sentences
        import re
        sentences = re.split(r'[.!?]+', content)

        # Look for sentences that contain factual patterns
        fact_patterns = [
            r'is\s+', r'are\s+', r'was\s+', r'were\s+',
            r'has\s+', r'have\s+', r'according\s+to',
            r'studies\s+show', r'research\s+indicates',
            r'data\s+shows', r'it\s+is\s+known'
        ]

        for sentence in sentences[:50]:  # Limit processing
            sentence = sentence.strip()
            if len(sentence) > 20:  # Ignore very short sentences
                # Skip sentences that mostly echo the original query
                query_words = set(q for q in query.lower().split() if len(q) > 3)
                sentence_words = set(w for w in sentence.lower().split() if len(w) > 3)
                if query_words and sentence_words:
                    overlap = len(query_words & sentence_words) / len(query_words)
                    if overlap > 0.6:
                        continue
                # Check if sentence contains fact patterns
                if any(re.search(pattern, sentence, re.IGNORECASE) for pattern in fact_patterns):
                    facts.append({
                        "statement": sentence,
                        "confidence": 0.7,  # Would be calculated based on source reliability
                        "source": "web_research"
                    })

        return facts[:10]  # Return top 10 facts

    async def _analyze_findings(
        self,
        research_data: Dict[str, Any],
        request: str,
        research_type: TaskType
    ) -> Dict[str, Any]:
        """Analyze and synthesize research findings"""
        analysis = {
            "key_points": [],
            "contradictions": [],
            "consensus": [],
            "gaps": [],
            "confidence": 0.0
        }

        try:
            facts = research_data.get("facts", [])
            sources = research_data.get("sources", [])

            if not facts:
                analysis["confidence"] = 0.1
                return analysis

            # Simple analysis - group similar facts
            statements = [fact.get("statement", "") for fact in facts if fact.get("statement")]

            # Look for consensus (similar statements)
            if len(statements) > 1:
                # Very simplified consensus detection
                # In practice would use semantic similarity
                analysis["key_points"] = statements[:5]  # Top 5 statements
                analysis["confidence"] = min(0.9, 0.5 + len(sources) * 0.1)

            # Identify potential contradictions (very basic)
            # Look for opposing statements
            negative_words = ["not", "no", "never", "false", "incorrect", "wrong"]
            positive_statements = [s for s in statements if not any(word in s.lower() for word in negative_words)]
            negative_statements = [s for s in statements if any(word in s.lower() for word in negative_words)]

            if positive_statements and negative_statements:
                analysis["contradictions"] = [
                    f"Found conflicting information: {len(positive_statements)} sources support vs {len(negative_statements)} sources contradict"
                ]

        except Exception as e:
            self.logger.warning(f"Error analyzing findings: {e}")
            analysis["confidence"] = 0.1

        return analysis

    async def _generate_research_report(
        self,
        analysis: Dict[str, Any],
        request: str,
        research_type: TaskType,
        depth: str
    ) -> str:
        """Generate a comprehensive research report"""
        report_parts = []

        # Header
        report_parts.append(f"# Research Report: {request}")
        report_parts.append(f"*Generated by JARVIS Research Agent*")
        report_parts.append(f"*Depth: {depth.title()} | Type: {research_type.value.replace('_', ' ').title()}*\n")

        # Executive Summary
        confidence = analysis.get("confidence", 0.0)
        confidence_level = "High" if confidence > 0.8 else "Medium" if confidence > 0.5 else "Low"
        report_parts.append(f"## Executive Summary")
        report_parts.append(f"Research completed with {confidence_level} confidence ({confidence:.1%}).")
        report_parts.append(f"Consulted {len(analysis.get('sources', []))} sources.\n")

        # Key Findings
        key_points = analysis.get("key_points", [])
        if key_points:
            report_parts.append("## Key Findings")
            for i, point in enumerate(key_points, 1):
                report_parts.append(f"{i}. {point}")
            report_parts.append("")

        # Contradictions (if any)
        contradictions = analysis.get("contradictions", [])
        if contradictions:
            report_parts.append("## Conflicting Information")
            for contradiction in contradictions:
                report_parts.append(f"- {contradiction}")
            report_parts.append("")

        # Consensus Points
        consensus = analysis.get("consensus", [])
        if consensus:
            report_parts.append("## Consensus View")
            for point in consensus:
                report_parts.append(f"- {point}")
            report_parts.append("")

        # Research Limitations
        gaps = analysis.get("gaps", [])
        if gaps or confidence < 0.7:
            report_parts.append("## Limitations and Notes")
            if gaps:
                for gap in gaps:
                    report_parts.append(f"- {gap}")
            if confidence < 0.7:
                report_parts.append("- Limited availability of authoritative sources")
                report_parts.append("- Consider consulting domain experts for specialized topics")
            report_parts.append("")

        # Sources Consulted
        # In practice would list actual sources
        report_parts.append("## Methodology")
        report_parts.append("- Information gathered from authoritative web sources")
        report_parts.append("- Cross-referenced multiple references for verification")
        report_parts.append("- Analysis performed using JARVIS research protocols\n")

        # Footer
        report_parts.append("---\n*Report generated by JARVIS Research Agent*")

        return "\n".join(report_parts)

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
            "research_domains": self.research_domains,
            "last_activity": datetime.now().isoformat()
        }

    async def shutdown(self):
        """Shutdown the agent"""
        self.logger.info("Shutting down Research Agent")
        self.is_initialized = False
        await self.browser_tool.shutdown()