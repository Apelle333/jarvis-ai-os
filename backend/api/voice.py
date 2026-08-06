"""
JARVIS AI Operating System - Voice API
Handles the real voice workflow: STT -> Brain -> TTS with live WS state events.
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from pydantic import BaseModel

from agents.main_agent import MainAgent
from api.dependencies import get_brain, get_main_agent
from voice.pipeline import VoicePipeline
from voice.whisper import WhisperSTT
from voice.piper import PiperTTS

logger = logging.getLogger(__name__)

router = APIRouter()

# Global instances
whisper_stt: Optional[WhisperSTT] = None
piper_tts: Optional[PiperTTS] = None
voice_pipeline: Optional[VoicePipeline] = None


class TTSRequest(BaseModel):
    text: str
    voice: str = "en_US-lessac-medium"
    speed: float = 1.0


def get_stt() -> WhisperSTT:
    """Dependency to get the speech-to-text instance"""
    global whisper_stt
    if whisper_stt is None:
        whisper_stt = WhisperSTT()
    return whisper_stt


def get_tts() -> PiperTTS:
    """Dependency to get the text-to-speech instance"""
    global piper_tts
    if piper_tts is None:
        piper_tts = PiperTTS()
    return piper_tts


def get_pipeline(
    agent: MainAgent = Depends(get_main_agent),
    stt: WhisperSTT = Depends(get_stt),
    tts: PiperTTS = Depends(get_tts),
) -> VoicePipeline:
    """Dependency to get the shared voice pipeline"""
    global voice_pipeline
    if voice_pipeline is None:
        voice_pipeline = VoicePipeline(stt=stt, agent=agent, tts=tts)
    return voice_pipeline


@router.post("/speech-to-text")
async def speech_to_text(
    audio: UploadFile = File(...),
    language: str = "en",
    stt: WhisperSTT = Depends(get_stt),
):
    """
    Convert speech to text
    """
    try:
        # Read audio file
        audio_data = await audio.read()

        # Convert speech to text
        text = await stt.transcribe(audio_data, language=language)

        return {
            "text": text,
            "language": language,
            "status": "success"
        }

    except Exception as e:
        logger.error(f"Error in speech-to-text: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process-voice")
async def process_voice(
    audio: UploadFile = File(...),
    language: str = "en",
    client_id: str = "",
    pipeline: VoicePipeline = Depends(get_pipeline),
):
    """
    Full voice round-trip: STT -> JARVIS Brain -> TTS.

    Emits ``voice_state`` events over the WebSocket connection matching
    ``client_id`` (listening/processing/speaking/error) and returns the
    response text plus base64 WAV audio for playback.
    """
    try:
        logger.info("Processing voice request")
        audio_data = await audio.read()

        if not audio_data:
            raise HTTPException(status_code=400, detail="Empty audio upload")

        result = await pipeline.run(
            audio_bytes=audio_data,
            language=language,
            client_id=client_id,
        )

        return {
            "text": result["text"],
            "response": result["response"],
            "audio": result["audio"],
            "audio_mime": result["audio_mime"],
            "audio_available": result.get("audio_available", False),
            "agent": result.get("agent"),
            "timestamp": result.get("timestamp"),
            "metadata": result.get("metadata"),
        }

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Voice request rejected: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing voice: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/text-to-speech")
async def text_to_speech(
    request: TTSRequest,
    tts: PiperTTS = Depends(get_tts),
):
    """
    Convert text to speech and return the WAV bytes directly.
    """
    try:
        audio_data = await tts.synthesize(
            text=request.text,
            voice=request.voice,
            speed=request.speed,
        )
        if not audio_data:
            raise HTTPException(status_code=500, detail="TTS produced no audio")

        return Response(
            content=audio_data,
            media_type="audio/wav",
            headers={"X-Text-Length": str(len(request.text))},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in text-to-speech: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voices")
async def get_available_voices(tts: PiperTTS = Depends(get_tts)):
    """
    Get available TTS voices
    """
    try:
        voices = await tts.get_available_voices()
        return {
            "voices": voices,
            "count": len(voices)
        }
    except Exception as e:
        logger.error(f"Error getting voices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_voice_status(
    pipeline: VoicePipeline = Depends(get_pipeline),
    agent: MainAgent = Depends(get_main_agent),
):
    """
    Get the status of the voice system (pipeline, STT, TTS)
    """
    try:
        agent_status = await agent.get_status() if agent else {}
        pipeline_status = await pipeline.get_status()

        return {
            "agent": agent_status,
            "pipeline": pipeline_status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting voice status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
