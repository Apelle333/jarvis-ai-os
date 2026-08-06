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
import os
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
        """Fire a voice_state event to the requesting client (or broadcast).

        state values: idle, listening, transcribing, thinking, speaking, error
        """
        message: Dict[str, Any] = {
            "type": "voice_state",
            "state": state,
            "timestamp": datetime.now().isoformat(),
        }
        message.update(payload)

        if client_id:
            # Fire-and-forget to avoid blocking pipeline
            asyncio.create_task(manager.send_personal_message(message, client_id))
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
        # Emit listening state (audio received)
        self._emit(client_id, "listening")

        # Transcription (Whisper)
        self._emit(client_id, "transcribing")
        text = ""
        try:
            stt_timeout = int(os.getenv('JARVIS_VOICE_STT_TIMEOUT', '30'))
            text = await asyncio.wait_for(self.stt.transcribe(audio_bytes, language=language), timeout=stt_timeout)
            text = (text or "").strip()
        except asyncio.TimeoutError:
            self.logger.error("STT timed out")
            self._emit(client_id, "error", message="Transcription timed out")
            return {
                "text": "",
                "response": "",
                "audio": "",
                "audio_mime": "audio/wav",
                "agent": None,
                "timestamp": datetime.now().isoformat(),
                "metadata": {},
                "error": "STT timeout"
            }
        except Exception as e:
            self.logger.error(f"STT error: {e}")
            self._emit(client_id, "error", message="Transcription error")
            return {
                "text": "",
                "response": "",
                "audio": "",
                "audio_mime": "audio/wav",
                "agent": None,
                "timestamp": datetime.now().isoformat(),
                "metadata": {},
                "error": f"STT error: {e}"
            }

        if not text:
            self._emit(client_id, "error", message="No speech detected")
            return {
                "text": "",
                "response": "",
                "audio": "",
                "audio_mime": "audio/wav",
                "agent": None,
                "timestamp": datetime.now().isoformat(),
                "metadata": {},
                "error": "no_speech_detected"
            }

        self._emit(client_id, "processing", event="transcription", text=text)
        self.logger.info(f"Voice -> text: {text[:100]}")

        # Brain (main agent -> planner -> model router -> swarm).
        self._emit(client_id, "thinking")
        result = {}
        response_text = ""
        try:
            agent_timeout = int(os.getenv('JARVIS_VOICE_AGENT_TIMEOUT', '120'))
            result = await asyncio.wait_for(
                self.agent.process_message(user_input=text, modality="voice"),
                timeout=agent_timeout,
            )
            response_text = result.get("response", "")
        except asyncio.TimeoutError:
            self.logger.error("Agent processing timed out")
            self._emit(client_id, "error", message="Agent processing timed out")
            response_text = "Sorry, I couldn't process that right now."
        except Exception as e:
            self.logger.error(f"Agent error: {e}")
            self._emit(client_id, "error", message="Agent processing error")
            response_text = "Sorry, I couldn't process that right now."

        # Speech synthesis (Piper).
        self._emit(client_id, "speaking", text=response_text)
        self.logger.info("Synthesizing voice response via Piper")

        audio_bytes_out = b""
        try:
            tts_timeout = int(os.getenv('JARVIS_VOICE_TTS_TIMEOUT', '30'))
            audio_bytes_out = await asyncio.wait_for(
                self.tts.synthesize(text=response_text, voice=settings.tts_voice, speed=settings.tts_speed),
                timeout=tts_timeout,
            )
        except asyncio.TimeoutError:
            self.logger.error("TTS timed out")
            self._emit(client_id, "error", message="TTS timed out")
            audio_bytes_out = b""
        except Exception as e:
            self.logger.error(f"TTS failed: {e}")
            self._emit(client_id, "error", message="TTS error")
            audio_bytes_out = b""

        # Done - return structured result. Emit idle state
        self._emit(client_id, "idle")

        return {
            "text": text,
            "response": response_text,
            "audio": base64.b64encode(audio_bytes_out).decode("ascii"),
            "audio_mime": "audio/wav",
            "agent": result.get("agent") if isinstance(result, dict) else None,
            "timestamp": result.get("timestamp") if isinstance(result, dict) else datetime.now().isoformat(),
            "metadata": result.get("metadata") if isinstance(result, dict) else {},
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
