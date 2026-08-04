"""
JARVIS AI Operating System - Security Agent
Specialized agent for cybersecurity tasks
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

if TYPE_CHECKING:
    from core.brain import JARVIS_Brain

logger = logging.getLogger(__name__)


class SecurityAgent:
    """
    Security Agent - Specialized cybersecurity agent
    Handles security assessments, vulnerability analysis, threat modeling, and security recommendations
    """

    def __init__(self, brain: JARVIS_Brain):
        self.brain = brain
        self.logger = logging.getLogger(__name__)
        self.personality = Personality()
        self.memory_manager = MemoryManager()
        self.model_router = ModelRouter()
        self.is_initialized = False

        # Agent metadata
        self.agent_id = "security_agent"
        self.agent_name = "Security Specialist"
        self.agent_type = "specialist"
        self.specializations = [
            "vulnerability_assessment",
            "threat_modeling",
            "security_review",
            "incident_response",
            "security_architecture",
            "compliance_checking",
            "penetration_testing",
            "malware_analysis",
            "network_security",
            "application_security"
        ]

        # Security frameworks and standards
        self.security_frameworks = [
            "OWASP", "NIST", "ISO 27001", "CIS Controls", "SANS",
            "PCI DSS", "HIPAA", "GDPR", "SOC 2"
        ]

    async def initialize(self):
        """Initialize the security agent"""
        try:
            self.logger.info("Initializing Security Agent...")
            await self.personality.initialize()
            await self.memory_manager.initialize()
            await self.model_router.initialize()
            self.is_initialized = True
            self.logger.info("Security Agent initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Security Agent: {e}")
            raise

    async def process_request(
        self,
        request: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a security-related request

        Args:
            request: The security request from user
            context: Additional context (code, systems, configurations, etc.)

        Returns:
            Dictionary containing response and metadata
        """
        if not self.is_initialized:
            await self.initialize()

        try:
            self.logger.info(f"Security Agent processing request: {request[:100]}...")

            # Analyze the request to determine security task type
            security_type = await self._classify_security_task(request)
            urgency = await self._assess_urgency(request, context)

            # Store request in memory
            await self.memory_manager.store_conversation(
                role="user",
                content=request,
                modality="text",
                timestamp=datetime.now(),
                metadata={"agent": self.agent_id, "security_type": security_type.value}
            )

            # Get relevant context from memory
            memory_context = await self.memory_manager.get_recent_context(limit=10)
            if context:
                memory_context.append(context)

            # Route to appropriate model for security tasks
            model_selection = await self.model_router.select_model(
                task_type=TaskType.RESEARCH,  # Security often involves research and analysis
                complexity=urgency,
                context=memory_context
            )

            # Perform security analysis
            security_analysis = await self._perform_security_analysis(
                request, security_type, context, memory_context
            )

            # Generate security report/recommendations
            security_report = await self._generate_security_report(
                security_analysis, request, security_type, urgency
            )

            # Apply personality to response
            personalized_response = await self.personality.apply_personality(
                security_report, memory_context, request
            )

            # Store response
            await self.memory_manager.store_conversation(
                role="assistant",
                content=personalized_response,
                modality="text",
                timestamp=datetime.now(),
                metadata={
                    "agent": self.agent_id,
                    "security_type": security_type.value,
                    "urgency": urgency,
                    "model_used": model_selection.model_name,
                    "risk_level": security_analysis.get("risk_level", "unknown")
                }
            )

            return {
                "response": personalized_response,
                "agent": self.agent_id,
                "agent_name": self.agent_name,
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "security_type": security_type.value,
                    "urgency": urgency,
                    "model_used": model_selection.model_name,
                    "reason": model_selection.reason,
                    "risk_level": security_analysis.get("risk_level", "unknown"),
                    "confidence": security_analysis.get("confidence", 0.0)
                }
            }

        except Exception as e:
            self.logger.error(f"Error in Security Agent processing: {e}", exc_info=True)
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

    async def _classify_security_task(self, request: str) -> TaskType:
        """Classify the type of security task"""
        request_lower = request.lower()

        # Security task classification
        if any(word in request_lower for word in ["vulnerability", "exploit", "weakness", "flaw", "bug"]):
            # Could map to a specific task type, but we'll use RESEARCH for now
            return TaskType.RESEARCH
        elif any(word in request_lower for word in ["threat", "attack", "risk", "danger"]):
            return TaskType.RESEARCH
        elif any(word in request_lower for word in ["audit", "review", "assessment", "check"]):
            return TaskType.RESEARCH
        elif any(word in request_lower for word in ["incident", "breach", "compromise"]):
            return TaskType.RESEARCH
        elif any(word in request_lower for word in ["compliance", "regulation", "standard", "policy"]):
            return TaskType.RESEARCH
        elif any(word in request_lower for word in ["secure", "protect", "defend", "harden"]):
            return TaskType.RESEARCH
        else:
            return TaskType.RESEARCH  # Default to research for security tasks

    async def _assess_urgency(self, request: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Assess the urgency of the security request"""
        request_lower = request.lower()
        urgency_indicators = {
            "low": ["general", "information", "learn", "understand", "overview"],
            "medium": ["check", "review", "assess", "evaluate", "improve"],
            "high": ["urgent", "immediate", "critical", "emergency", "breach", "attack"],
            "critical": ["active", "ongoing", "exploit", "compromised", "infected"]
        }

        # Check for explicit urgency indicators
        for urgency_level, indicators in urgency_indicators.items():
            if any(indicator in request_lower for indicator in indicators):
                return urgency_level

        # Implicit urgency based on context
        if context:
            if context.get("incident_active") or context.get("breach_detected"):
                return "critical"
            if context.get("production_system") or context.get("live_site"):
                return "high"

        return "medium"  # Default

    async def _perform_security_analysis(
        self,
        request: str,
        security_type: TaskType,
        context: Optional[Dict[str, Any]],
        memory_context: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Perform security analysis based on the request type"""
        analysis = {
            "findings": [],
            "risk_level": "low",
            "confidence": 0.0,
            "recommendations": [],
            "references": []
        }

        try:
            # Route to specialized analysis based on security type
            if "vulnerability" in request.lower() or "exploit" in request.lower():
                analysis = await self._analyze_vulnerabilities(request, context)
            elif "threat" in request.lower() or "risk" in request.lower():
                analysis = await self._analyze_threats(request, context)
            elif "compliance" in request.lower() or "regulation" in request.lower():
                analysis = await self._analyze_compliance(request, context)
            elif "code" in str(context) or "script" in request.lower():
                analysis = await self._analyze_code_security(request, context)
            else:
                # General security analysis
                analysis = await self._general_security_analysis(request, context)

        except Exception as e:
            self.logger.warning(f"Error performing security analysis: {e}")
            analysis["confidence"] = 0.1
            analysis["findings"] = [f"Analysis encountered an error: {str(e)}"]

        return analysis

    async def _analyze_vulnerabilities(self, request: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze potential vulnerabilities"""
        analysis = {
            "findings": [],
            "risk_level": "medium",
            "confidence": 0.7,
            "recommendations": [],
            "references": ["OWASP Top 10", "CWE/SANS Top 25"]
        }

        # Context-aware analysis
        if context:
            if "code" in context:
                analysis["findings"].append("Code review recommended for common vulnerabilities")
                analysis["recommendations"].append("Apply input validation and output encoding")
                analysis["recommendations"].append("Use parameterized queries to prevent SQL injection")
                analysis["recommendations"].append("Implement proper authentication and session management")

            if "network" in context:
                analysis["findings"].append("Network configuration review recommended")
                analysis["recommendations"].append("Implement firewall rules and network segmentation")
                analysis["recommendations"].append("Use encryption for data in transit")
                analysis["recommendations"].append("Regular vulnerability scanning of network devices")

        # General vulnerability findings
        analysis["findings"].extend([
            "Regular security assessments recommended",
            "Keep systems and software updated",
            "Implement least privilege access controls",
            "Enable logging and monitoring"
        ])

        return analysis

    async def _analyze_threats(self, request: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze potential threats"""
        analysis = {
            "findings": [],
            "risk_level": "medium",
            "confidence": 0.7,
            "recommendations": [],
            "references": ["MITRE ATT&CK Framework", "Cyber Kill Chain"]
        }

        analysis["findings"].extend([
            "Threat modeling recommended for critical assets",
            "Implement intrusion detection and prevention systems",
            "Regular security awareness training for personnel",
            "Develop and test incident response plans"
        ])

        analysis["recommendations"].extend([
            "Conduct regular threat intelligence gathering",
            "Implement multi-factor authentication",
            "Use endpoint detection and response (EDR) solutions",
            "Establish security operations center (SOC) capabilities"
        ])

        return analysis

    async def _analyze_compliance(self, request: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze compliance requirements"""
        analysis = {
            "findings": [],
            "risk_level": "low",
            "confidence": 0.8,
            "recommendations": [],
            "references": []
        }

        # Determine which compliance framework is relevant
        request_lower = request.lower()
        frameworks = []
        if "hipaa" in request_lower:
            frameworks.append("HIPAA")
            analysis["references"].append("HIPAA Security Rule")
        if "pci" in request_lower or "payment" in request_lower:
            frameworks.append("PCI DSS")
            analysis["references"].append("PCI DSS Requirements")
        if "gdpr" in request_lower or "data protection" in request_lower:
            frameworks.append("GDPR")
            analysis["references"].append("GDPR Articles 32-34")
        if "sox" in request_lower or "financial" in request_lower:
            frameworks.append("SOX")
            analysis["references"].append("SOX Section 404")
        if not frameworks:
            frameworks.append("General Security Best Practices")
            analysis["references"].append("NIST Cybersecurity Framework")
            analysis["references"].append("ISO 27001/27002")

        analysis["findings"].append(f"Compliance assessment for: {', '.join(frameworks)}")
        analysis["recommendations"].extend([
            "Conduct gap analysis against required standards",
            "Implement required security controls",
            "Establish continuous compliance monitoring",
            "Document policies and procedures",
            "Regular compliance audits and assessments"
        ])

        return analysis

    async def _analyze_code_security(self, request: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze code for security issues"""
        analysis = {
            "findings": [],
            "risk_level": "medium",
            "confidence": 0.75,
            "recommendations": [],
            "references": ["OWASP Code Review Guide", "CERT Secure Coding Standards"]
        }

        analysis["findings"].extend([
            "Static code analysis recommended",
            "Review for common vulnerabilities (SQLi, XSS, CSRF, etc.)",
            "Check for insecure dependencies",
            "Review authentication and authorization implementations"
        ])

        analysis["recommendations"].extend([
            "Implement secure coding practices training",
            "Use static application security testing (SAST) tools",
            "Conduct regular code reviews with security focus",
            "Implement dependency scanning and vulnerability management",
            "Use web application firewalls (WAF) for runtime protection"
        ])

        return analysis

    async def _general_security_analysis(self, request: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform general security analysis"""
        analysis = {
            "findings": [],
            "risk_level": "low",
            "confidence": 0.6,
            "recommendations": [],
            "references": ["NIST Cybersecurity Framework", "ISO 27001"]
        }

        analysis["findings"].extend([
            "Defense-in-depth approach recommended",
            "Regular security assessments and testing",
            "Employee security awareness training",
            "Incident response planning and testing"
        ])

        analysis["recommendations"].extend([
            "Implement comprehensive security policy",
            "Use multi-factor authentication everywhere possible",
            "Encrypt sensitive data at rest and in transit",
            "Regular backup and disaster recovery testing",
            "Continuous security monitoring and logging"
        ])

        return analysis

    async def _generate_security_report(
        self,
        analysis: Dict[str, Any],
        request: str,
        security_type: TaskType,
        urgency: str
    ) -> str:
        """Generate a comprehensive security report"""
        report_parts = []

        # Header
        risk_level = analysis.get("risk_level", "unknown").upper()
        urgency_level = urgency.upper()
        report_parts.append(f"# Security Analysis Report")
        report_parts.append(f"**Request:** {request}")
        report_parts.append(f"**Risk Level:** {risk_level}")
        report_parts.append(f"**Urgency:** {urgency_level}")
        report_parts.append(f"*Generated by JARVIS Security Agent*\n")

        # Executive Summary
        confidence = analysis.get("confidence", 0.0)
        conf_level = "High" if confidence > 0.8 else "Medium" if confidence > 0.5 else "Low"
        report_parts.append(f"## Executive Summary")
        report_parts.append(f"Security analysis completed with {conf_level} confidence ({confidence:.1%}).")
        report_parts.append(f"Primary concern: {security_type.value.replace('_', ' ').title()}\n")

        # Findings
        findings = analysis.get("findings", [])
        if findings:
            report_parts.append("## Key Findings")
            for i, finding in enumerate(findings, 1):
                report_parts.append(f"{i}. {finding}")
            report_parts.append("")

        # Risk Assessment
        report_parts.append("## Risk Assessment")
        risk_level = analysis.get("risk_level", "unknown")
        risk_descriptions = {
            "low": "Minimal risk - standard security practices sufficient",
            "medium": "Moderate risk - targeted security measures recommended",
            "high": "High risk - immediate action required",
            "critical": "Critical risk - emergency response needed"
        }
        report_parts.append(f"**Risk Level:** {risk_level.title()}")
        report_parts.append(f"**Assessment:** {risk_descriptions.get(risk_level, 'Risk level not determined')}\n")

        # Recommendations
        recommendations = analysis.get("recommendations", [])
        if recommendations:
            report_parts.append("## Recommendations")
            for i, rec in enumerate(recommendations, 1):
                report_parts.append(f"{i}. {rec}")
            report_parts.append("")

        # References
        references = analysis.get("references", [])
        if references:
            report_parts.append("## References and Standards")
            for ref in references:
                report_parts.append(f"- {ref}")
            report_parts.append("")

        # Next Steps based on urgency
        if urgency in ["high", "critical"]:
            report_parts.append("## Immediate Actions Required")
            if urgency == "critical":
                report_parts.append("1. **EMERGENCY**: Isolate affected systems immediately")
                report_parts.append("2. **CONTACT**: Notify incident response team and management")
                report_parts.append("3. **EVIDENCE**: Preserve all logs and potential evidence")
                report_parts.append("4. **RESPONSE**: Activate incident response plan")
            else:
                report_parts.append("1. Prioritize addressing high-risk findings")
                report_parts.append("2. Schedule remediation within recommended timeframe")
                report_parts.append("3. Implement monitoring for detecting exploitation attempts")
            report_parts.append("")

        # Footer
        report_parts.append("---\n*Report generated by JARVIS Security Agent*")
        report_parts.append("*Note: This analysis is for informational purposes. Consult with certified security professionals for critical security decisions.*")

        return "\n".join(report_parts)

    async def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "agent_type": self.agent_type,
            "is_initialized": self.is_initialized,
            "specializations": self.specializations,
            "security_frameworks": self.security_frameworks,
            "last_activity": datetime.now().isoformat()
        }

    async def shutdown(self):
        """Shutdown the agent"""
        self.logger.info("Shutting down Security Agent")
        self.is_initialized = False