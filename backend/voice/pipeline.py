"""
JARVIS AI Operating System - Voice Pipeline
Orchestrates the complete local voice workflow:

    Microphone
        -> Whisper STT
        -> JARVIS Brain (main agent -> model router)
        -> Piper TTS
        -> audio bytes

Emits real-time ``voice_state`` events over the existing WebSocket
infrastructure so the frontend HUD can reflect listening / processing /
speaking / error states.
"""

import asyncio
import base64
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from api.websocket import manager
from core.settings import settings

logger = logging.getLogger(__name__)


class VoicePipeline:
    """
    Connects the existing STT / brain / TTS modules into one callable flow.
    """

    def __init__(self, stt, agent, tts):
        self.stt = stt
        self.agent = agent
        self.tts = tts
        self.logger = logging.getLogger(__name__)

    def _emit(self, client_id: str, state: str, **payload: Any) -> None:
        """Fire a voice_state event to the requesting client (or broadcast)."""
        message: Dict[str, Any] = {
            "type": "voice_state",
            "state": state,
            "timestamp": datetime.now().isoformat(),
        }
        message.update(payload)

        if client_id:
            asyncio.create_task(
                manager.send_personal_message(message, client_id)
            )
        else:
            asyncio.create_task(manager.broadcast(message))

    async def run(
        self,
        audio_bytes: bytes,
        language: str = "en",
        client_id: str = "",
    ) -> Dict[str, Any]:
        """
        Run the full voice round-trip for a single spoken utterance.

        Returns:
            dict with ``text`` (transcription), ``response`` (brain reply),
            ``audio`` (base64 WAV bytes), and metadata.
        """
        # Transcription (Whisper) -- long enough that the ring should pulse.
        self._emit(client_id, "processing")

        text = await self.stt.transcribe(audio_bytes, language=language)
        text = (text or "").strip()

        if not text:
            self._emit(client_id, "error", message="No speech detected")
            raise ValueError("No speech detected in audio")

        self._emit(
            client_id,
            "processing",
            event="transcription",
            text=text,
        )
        self.logger.info(f"Voice -> text: {text[:100]}")

        # Brain (main agent -> planner -> model router -> swarm).
        result = await self.agent.process_message(
            user_input=text,
            modality="voice",
        )
        response_text = result.get("response", "")

        # Speech synthesis (Piper).
        self._emit(client_id, "speaking", text=response_text)
        self.logger.info("Synthesizing voice response via Piper")

        try:
            audio_bytes_out = await self.tts.synthesize(
                text=response_text,
                voice=settings.tts_voice,
                speed=settings.tts_speed,
            )
        except Exception as e:
            self.logger.error(f"TTS failed: {e}")
            audio_bytes_out = b""

        return {
            "text": text,
            "response": response_text,
            "audio": base64.b64encode(audio_bytes_out).decode("ascii"),
            "audio_mime": "audio/wav",
            "agent": result.get("agent"),
            "timestamp": result.get("timestamp"),
            "metadata": result.get("metadata"),
        }

    async def get_status(self) -> Dict[str, Any]:
        """Status of each pipeline stage."""
        stt_status = {}
        tts_status = {}
        try:
            stt_status = await self.stt.get_status()
        except Exception as e:
            stt_status = {"status": "error", "error": str(e)}
        try:
            tts_status = await self.tts.get_status()
        except Exception as e:
            tts_status = {"status": "error", "error": str(e)}

        return {
            "speech_to_text": stt_status,
            "text_to_speech": tts_status,
            "status": (
                "ready"
                if stt_status.get("status") == "ready"
                and tts_status.get("status") == "ready"
                else "degraded"
            ),
        }
