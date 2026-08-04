"""
JARVIS AI Operating System - Speech to Text (Whisper)
Handles speech recognition using OpenAI Whisper
"""

import asyncio
import io
import logging
import numpy as np
from typing import Dict, Any, Optional, List
import av
import whisper

from core.settings import settings

logger = logging.getLogger(__name__)


class WhisperSTT:
    """
    Speech-to-Text using OpenAI Whisper
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.is_initialized = False
        self.model = None
        self.model_name = settings.speech_recognition_model or "base"  # Default model
        self.supported_languages = {
            "en": "english",
            "es": "spanish",
            "fr": "french",
            "de": "german",
            "it": "italian",
            "pt": "portuguese",
            "pl": "polish",
            "nl": "dutch",
            "ar": "arabic",
            "zh": "chinese",
            "ja": "japanese",
            "ko": "korean",
            "ru": "russian"
        }

    async def initialize(self):
        """Initialize the Whisper model"""
        try:
            self.logger.info(f"Initializing Whisper STT with model '{self.model_name}'...")
            # Load the model in a thread to avoid blocking
            loop = asyncio.get_running_loop()
            self.model = await loop.run_in_executor(
                None,
                lambda: whisper.load_model(self.model_name)
            )
            self.is_initialized = True
            self.logger.info("Whisper STT initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Whisper STT: {e}")
            raise

    def _decode_audio_f32(self, audio_data: bytes) -> np.ndarray:
        """
        Decode audio bytes (any format Whisper's decoder supports) to 16kHz
        mono float32 in-process via PyAV.

        This avoids shelling out to the ffmpeg binary, which would otherwise
        spawn a console window under a windowless (pythonw) backend.
        """
        if not audio_data:
            return np.zeros(0, dtype=np.float32)

        try:
            container = av.open(io.BytesIO(audio_data))
            stream = next(
                (s for s in container.streams.audio if s.codec_context is not None),
                None,
            )
            if stream is None:
                return np.zeros(0, dtype=np.float32)

            resampler = av.AudioResampler(
                format="fltp", layout="mono", rate=16000
            )

            chunks = []
            for frame in container.decode(stream):
                for out_frame in resampler.resample(frame):
                    arr = out_frame.to_ndarray().reshape(-1)
                    chunks.append(arr)

            for out_frame in resampler.resample(None):
                chunks.append(out_frame.to_ndarray().reshape(-1))

            if not chunks:
                return np.zeros(0, dtype=np.float32)

            return np.concatenate(chunks).astype(np.float32)

        except Exception as e:
            self.logger.error(f"Failed to decode audio with PyAV: {e}")
            raise

    async def transcribe(
        self,
        audio_data: bytes,
        language: str = "en",
        task: str = "transcribe"
    ) -> str:
        """
        Transcribe audio to text

        Args:
            audio_data: Raw audio bytes (WAV, WebM/Opus, etc.)
            language: Language code (e.g., 'en' for English)
            task: Either 'transcribe' or 'translate'

        Returns:
            Transcribed text
        """
        if not self.is_initialized:
            await self.initialize()

        try:
            audio_np = self._decode_audio_f32(audio_data)
            if audio_np.size == 0:
                return ""

            # Transcribe in a thread to avoid blocking.
            # Passing a numpy array (instead of a file path) keeps decoding
            # in-process and never invokes the ffmpeg CLI.
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.model.transcribe(
                    audio_np,
                    language=language if language != "auto" else None,
                    task=task
                )
            )

            text = result["text"].strip()
            self.logger.info(f"Transcribed audio: {text[:100]}...")
            return text

        except Exception as e:
            self.logger.error(f"Error transcribing audio: {e}", exc_info=True)
            raise

    async def detect_language(self, audio_data: bytes) -> Dict[str, Any]:
        """
        Detect the language of the audio

        Args:
            audio_data: Raw audio bytes

        Returns:
            Dictionary with language detection results
        """
        if not self.is_initialized:
            await self.initialize()

        try:
            audio_np = self._decode_audio_f32(audio_data)
            if audio_np.size == 0:
                return {
                    "language": "unknown",
                    "language_probability": 0.0,
                    "is_reliable": False,
                }

            # Detect language in a thread
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.model.transcribe(
                    audio_np,
                    task="transcribe"
                )
            )

            language = result.get("language", "unknown")
            language_probability = max(
                [v for k, v in result.items() if k.endswith("_prob") and isinstance(v, float)],
                default=0.0
            )

            return {
                "language": language,
                "language_probability": language_probability,
                "is_reliable": language_probability > 0.5
            }

        except Exception as e:
            self.logger.error(f"Error detecting language: {e}", exc_info=True)
            raise

    async def get_available_models(self) -> List[str]:
        """Get list of available Whisper models"""
        return ["tiny", "base", "small", "medium", "large"]

    async def change_model(self, model_name: str) -> bool:
        """
        Change the Whisper model

        Args:
            model_name: Name of the model to use

        Returns:
            True if successful
        """
        if model_name not in await self.get_available_models():
            raise ValueError(f"Unsupported model: {model_name}")

        try:
            self.logger.info(f"Switching Whisper model from {self.model_name} to {model_name}")
            # Unload current model
            if self.model is not None:
                del self.model
                self.model = None

            # Load new model
            self.model_name = model_name
            await self.initialize()
            return True

        except Exception as e:
            self.logger.error(f"Error changing Whisper model: {e}")
            # Try to restore previous model if possible
            try:
                await self.initialize()
            except:
                pass
            raise

    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        if not self.is_initialized:
            await self.initialize()

        return {
            "model_name": self.model_name,
            "is_loaded": self.model is not None,
            "supported_languages": list(self.supported_languages.keys()),
            "supported_tasks": ["transcribe", "translate"]
        }

    async def get_status(self) -> Dict[str, Any]:
        """Get status of the speech-to-text system"""
        return {
            "model": self.model_name,
            "is_initialized": self.is_initialized,
            "model_loaded": self.model is not None,
            "supported_languages": list(self.supported_languages.keys()),
            "status": "ready" if self.is_initialized else "not_initialized"
        }

    async def shutdown(self):
        """Shutdown the Whisper STT"""
        self.logger.info("Shutting down Whisper STT")
        self.is_initialized = False
        if self.model is not None:
            del self.model
            self.model = None