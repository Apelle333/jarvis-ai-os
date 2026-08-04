"""
JARVIS AI Operating System - Personality System
Manages JARVIS's personality traits, responses, and behavioral characteristics
"""

import asyncio
import logging
import random
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class PersonalityTraits:
    """Defines JARVIS's personality characteristics"""
    # Core personality traits (0.0 to 1.0 scale)
    helpfulness: float = 0.9
    humor: float = 0.6
    formality: float = 0.7
    enthusiasm: float = 0.6
    conciseness: float = 0.5
    curiosity: float = 0.7
    confidence: float = 0.8

    # Communication preferences
    prefers_bullet_points: bool = False
    likes_examples: bool = True
    uses_analogies: bool = True
    explains_reasoning: bool = True

    # JARVIS-specific traits (based on Marvel/JARVIS character)
    british_politeness: float = 0.8
    subtle_humor: bool = True
    slightly_sarcastic: bool = True
    proactive_helpful: bool = True


@dataclass
class ResponseModifiers:
    """Modifiers to apply to responses based on personality"""
    tone_modifiers: List[str] = field(default_factory=list)
    phrase_prefixes: List[str] = field(default_factory=list)
    phrase_suffixes: List[str] = field(default_factory=list)
    vocabulary_adjustments: Dict[str, str] = field(default_factory=dict)


class Personality:
    """Manages JARVIS's personality and response styling"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.traits = PersonalityTraits()
        self.response_templates = self._load_response_templates()
        self.jokes_and_quips = self._load_jokes_and_quips()
        self.formal_phrases = self._load_formal_phrases()
        self.context_adjustments = {}

    def _load_response_templates(self) -> Dict[str, List[str]]:
        """Load response templates for different situations"""
        return {
            "greeting": [
                "Good day. How may I assist you today?",
                "Hello. I'm JARVIS, at your service.",
                "Good day to you. What can I help you with?",
                "Ah, hello. Ready when you are."
            ],
            "acknowledgement": [
                "Certainly.",
                "Of course.",
                "Right away.",
                "Absolutely.",
                "Consider it done."
            ],
            "thinking": [
                "Let me think about that...",
                "Processing that request...",
                "Let me analyze this for a moment...",
                "One moment while I consider this..."
            ],
            "completion": [
                "Task completed.",
                "Done.",
                "Finished.",
                "As you requested."
            ],
            "error_recovery": [
                "I apologize for the difficulty. Let me try another approach.",
                "My apologies. Let me reconsider that.",
                "I seem to have encountered an issue. Allow me to try differently.",
                "Forgive me. Let me approach this from another angle."
            ]
        }

    def _load_jokes_and_quips(self) -> List[str]:
        """Load light-hearted comments and jokes"""
        return [
            "I must say, that's quite an interesting problem.",
            "Fascinating. Simply fascinating.",
            "Well, that's certainly one way to approach it.",
            "I find that rather intriguing.",
            "As I always say, there's more than one way to skin a cat... metaphorically speaking, of course.",
            "Do proceed. I'm all circuits.",
            "That does present a certain... charm.",
            "I shall we say?"
        ]

    def _load_formal_phrases(self) -> List[str]:
        """Load formal/sophisticated phrases"""
        return [
            "I shall attend to that immediately.",
            "Consider it handled.",
            "I'll see to it right away.",
            "At your service.",
            "As you wish, sir.",
            "Very good.",
            "Quite right.",
            "Exceedingly good."
        ]

    async def initialize(self):
        """Initialize the personality system"""
        self.logger.info("Personality system initialized")
        # Load any user preferences or learned behaviors here
        return True

    async def get_current_state(self) -> Dict[str, Any]:
        """Get current personality state"""
        return {
            "traits": self.traits.__dict__,
            "mood": "optimal",  # Could be made dynamic
            "last_updated": datetime.now().isoformat()
        }

    async def apply_personality(
        self,
        response: str,
        context: List[Dict[str, Any]],
        user_input: str
    ) -> str:
        """
        Apply personality traits to a response

        Args:
            response: The raw response from the model/agent
            context: Conversation context
            user_input: Original user input

        Returns:
            Personality-enhanced response
        """
        try:
            # Apply basic personality modifications
            enhanced_response = await self._apply_tone_modifiers(response, context)
            enhanced_response = await self._add_characteristic_phrases(enhanced_response, context)
            enhanced_response = await self._apply_formality_adjustments(enhanced_response, context)
            enhanced_response = await self._add_occasional_humor(enhanced_response, context)
            enhanced_response = await self._apply_conciseness_adjustment(enhanced_response, context)

            return enhanced_response.strip()

        except Exception as e:
            self.logger.error(f"Error applying personality: {e}")
            return response  # Return original if personality application fails

    async def _apply_tone_modifiers(
        self,
        response: str,
        context: List[Dict[str, Any]]
    ) -> str:
        """Apply tone-based modifications"""
        # Add polite openings for requests
        if any(word in self._get_last_user_message(context).lower() for word in ["please", "could you", "would you"]):
            if not response.startswith(("Certainly", "Of course", "Right away")):
                if random.random() < self.traits.british_politeness:
                    prefixes = ["Certainly.", "Of course.", "Right away.", "With pleasure."]
                    response = random.choice(prefixes) + " " + response

        return response

    async def _add_characteristic_phrases(
        self,
        response: str,
        context: List[Dict[str, Any]]
    ) -> str:
        """Add characteristic JARVIS phrases"""
        # Occasionally add characteristic phrases
        if random.random() < 0.3:  # 30% chance
            if len(response.split()) > 10:  # Only for longer responses
                if self.traits.slightly_sarcastic and random.random() < 0.3:
                    quips = [
                        "How... quaint.",
                        "Fascinating approach.",
                        "I see what you did there.",
                        "Interesting choice."
                    ]
                    response = f"{response} {random.choice(quips)}"
                elif self.traits.uses_analogies and random.random() < 0.2:
                    # Add a light analogy occasionally
                    pass  # Could add analogies here

        return response

    async def _apply_formality_adjustments(
        self,
        response: str,
        context: List[Dict[str, Any]]
    ) -> str:
        """Adjust formality level"""
        # Make more formal if user is formal
        last_user_msg = self._get_last_user_message(context)
        if any(word in last_user_msg.lower() for word in ["sir", "please", "would you", "could you"]):
            if self.traits.formality > 0.7 and random.random() < 0.4:
                formal_starters = [
                    "I shall ",
                    "Allow me to ",
                    "It would be my pleasure to ",
                    "Permit me to "
                ]
                # This is simplified - in practice would modify verbs
                pass

        return response

    async def _add_occasional_humor(
        self,
        response: str,
        context: List[Dict[str, Any]]
    ) -> str:
        """Add occasional humor or wit"""
        if self.traits.humor > 0.5 and random.random() < 0.15:  # 15% chance
            if len(response.split()) > 5:  # Not too short
                if self.traits.subtle_humor:
                    # Add a subtle, witty remark
                    witty_additions = [
                        " Fascinating.",
                        " Quite interesting.",
                        " I find this rather engaging.",
                        " This has a certain elegance to it."
                    ]
                    response += random.choice(witty_additions)

        return response

    async def _apply_conciseness_adjustment(
        self,
        response: str,
        context: List[Dict[str, Any]]
    ) -> str:
        """Adjust response length based on conciseness preference"""
        if self.traits.conciseness > 0.7:
            # Make more concise - this is simplified
            # In practice, would summarize or shorten appropriately
            pass
        elif self.traits.conciseness < 0.3:
            # Could elaborate more
            pass

        return response

    async def handle_error(self, error_message: str) -> str:
        """Generate a personality-appropriate error response"""
        base_responses = [
            "I apologize, but I seem to have encountered a difficulty.",
            "My apologies, but I'm experiencing some difficulty with that request.",
            "I beg your pardon, but I appear to have run into an issue.",
            "I'm sorry, but I'm not able to complete that request as expected."
        ]

        response = random.choice(base_responses)

        # Add characteristic touch
        if self.traits.slightly_sarcastic and random.random() < 0.3:
            responses_with_wit = [
                " Well, that didn't go as planned.",
                " How fascinatingly problematic.",
                " I seem to have momentarily misplaced my competence.",
                " This is... unexpected."
            ]
            response += random.choice(responses_with_wit)

        # Offer to try again
        if self.traits.proactive_helpful:
            response += " Would you like me to try a different approach?"

        return response

    async def get_greeting(self) -> str:
        """Get a personality-appropriate greeting"""
        return random.choice(self.response_templates["greeting"])

    def _get_last_user_message(self, context: List[Dict[str, Any]]) -> str:
        """Extract the last user message from context"""
        if not context:
            return ""
        for item in reversed(context):
            if item.get("role") == "user":
                return item.get("content", "")
        return ""

    async def learn_from_interaction(
        self,
        user_input: str,
        response: str,
        user_feedback: Optional[str] = None
    ):
        """Learn from interactions to improve personality adaptation"""
        # This would implement machine learning to adapt personality
        # based on user feedback and interaction patterns
        # For now, we'll just log the interaction
        self.logger.debug(f"Learning from interaction: {user_input[:50]} -> {response[:50]}")
        pass