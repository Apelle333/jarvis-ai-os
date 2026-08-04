"""
JARVIS AI Operating System - Text to Speech (Piper)
Handles text-to-speech using Piper TTS
"""

import asyncio
import logging
import os
import subprocess
import tempfile
from typing import Dict, Any, List, Optional
import json
import wave

logger = logging.getLogger(__name__)

# Prevent console windows when spawning Piper from a windowless backend (pythonw).
_CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


class PiperTTS:
    """
    Text-to-Speech using Piper TTS
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.is_initialized = False
        self.piper_path = None  # Path to piper executable
        self.voices_dir = None  # Directory containing voice models
        self.default_voice = "en_US-lessac-medium"
        self.available_voices = {}
        self.voice_cache = {}  # Cache for loaded voices

    async def initialize(self):
        """Initialize the Piper TTS"""
        try:
            self.logger.info("Initializing Piper TTS...")
            # Find Piper executable
            await self._find_piper_executable()
            # Discover available voices
            await self._discover_voices()
            self.is_initialized = True
            self.logger.info("Piper TTS initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Piper TTS: {e}")
            # Don't raise - TTS is optional
            self.is_initialized = False
            self.logger.warning("Piper TTS initialization failed - TTS functionality will be limited")

    async def _find_piper_executable(self):
        """Find the Piper executable"""
        # Common locations for Piper
        possible_paths = [
            "piper",
            "./venv/Scripts/piper.exe",
            "venv/Scripts/piper.exe",
            "piper.exe",
            "./piper.exe",
            "./piper",
            "/usr/local/bin/piper",
            "/usr/bin/piper",
        ]

        for path in possible_paths:
            try:
                # Check if executable exists and works
                process = await asyncio.create_subprocess_exec(
                    path, "--help",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    creationflags=_CREATE_NO_WINDOW,
                )
                stdout, stderr = await process.communicate()
                if process.returncode == 0:
                    self.piper_path = path
                    self.logger.info(f"Found Piper executable at: {path}")
                    return
            except FileNotFoundError:
                continue
            except Exception:
                continue

        # If we get here, we didn't find Piper
        self.logger.warning("Piper executable not found - TTS will not be available")
        self.piper_path = None

    async def _discover_voices(self):
        """Discover available voice models"""
        if not self.piper_path:
            return

        # Common locations for voice models
        possible_voice_dirs = [
            "./voices",
            "../voices",
            "/usr/local/share/piper",
            "/usr/share/piper",
            "./piper_voices",
            "./models"
        ]

        for dir_path in possible_voice_dirs:
            if os.path.exists(dir_path) and os.path.isdir(dir_path):
                self.voices_dir = dir_path
                break

        if not self.voices_dir:
            self.logger.warning("Voice directory not found - using default voice only")
            self.voices_dir = "."  # Use current directory as fallback

        # Scan for .onnx files (Voice models)
        try:
            for file in os.listdir(self.voices_dir):
                if file.endswith(".onnx"):
                    voice_name = file[:-5]  # Remove .onnx extension
                    # Look for corresponding .onnx.json file
                    config_file = os.path.join(self.voices_dir, f"{voice_name}.onnx.json")
                    if os.path.exists(config_file):
                        try:
                            with open(config_file, 'r') as f:
                                config = json.load(f)
                            self.available_voices[voice_name] = {
                                "name": voice_name,
                                "model_path": os.path.join(self.voices_dir, f"{voice_name}.onnx"),
                                "config_path": config_file,
                                "config": config,
                                "language": config.get("language", "unknown"),
                                "speaker_count": config.get("speaker_id", {}).get("size", 1) if isinstance(config.get("speaker_id"), dict) else 1
                            }
                        except (json.JSONDecodeError, IOError):
                            # Still add the voice even if we can't read config
                            self.available_voices[voice_name] = {
                                "name": voice_name,
                                "model_path": os.path.join(self.voices_dir, f"{voice_name}.onnx"),
                                "config_path": config_file,
                                "config": {},
                                "language": "unknown",
                                "speaker_count": 1
                            }
        except Exception as e:
            self.logger.error(f"Error discovering voices: {e}")

        self.logger.info(f"Discovered {len(self.available_voices)} voices")
        if self.available_voices:
            self.logger.info(f"Available voices: {list(self.available_voices.keys())}")
        else:
            self.logger.warning("No voice models found")

    async def synthesize(
        self,
        text: str,
        voice: str = None,
        speed: float = 1.0,
        sample_rate: int = 22050
    ) -> bytes:
        """
        Synthesize text to speech

        Args:
            text: Text to synthesize
            voice: Voice name to use (defaults to default_voice)
            speed: Speech rate (1.0 = normal, >1.0 = faster, <1.0 = slower)
            sample_rate: Audio sample rate in Hz

        Returns:
            Audio data as WAV bytes
        """
        if not self.is_initialized:
            await self.initialize()

        if not self.piper_path:
            raise RuntimeError("Piper TTS is not available - executable not found")

        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        voice_name = voice or self.default_voice
        if voice_name not in self.available_voices:
            self.logger.warning(f"Voice '{voice_name}' not found, using default '{self.default_voice}'")
            voice_name = self.default_voice

        if voice_name not in self.available_voices:
            raise RuntimeError(f"No voices available - cannot synthesize speech")

        try:
            # Get voice info
            voice_info = self.available_voices[voice_name]
            model_path = voice_info["model_path"]

            # Create temporary files
            with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as text_file:
                text_file.write(text.encode('utf-8'))
                text_filename = text_file.name

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as audio_file:
                audio_filename = audio_file.name

            try:
                # Build Piper command
                cmd = [
                    self.piper_path,
                    "--model", model_path,
                    "--output_file", audio_filename
                ]

                # Add speaker ID if available (for multi-speaker models)
                voice_config = voice_info["config"]
                if "speaker_id" in voice_config and isinstance(voice_config["speaker_id"], dict):
                    # Default to speaker 0
                    speaker_id = 0
                    cmd.extend(["--speaker", str(speaker_id)])

                # Add length scale for speed control
                # Piper uses length_scale where 1.0 is normal, >1.0 is slower, <1.0 is faster
                length_scale = 1.0 / max(0.1, min(3.0, speed))  # Clamp speed between 0.33 and 3.0
                cmd.extend(["--length_scale", str(length_scale)])

                # Add noise scale for variation
                cmd.extend(["--noise_scale", "0.667"])
                cmd.extend(["--noise_w", "0.8"])

                # Process: pipe text file to Piper
                with open(text_filename, 'r', encoding='utf-8') as f:
                    process = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdin=subprocess.PIPE,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        creationflags=_CREATE_NO_WINDOW,
                    )

                    stdout, stderr = await process.communicate(input=f.read().encode('utf-8'))

                    if process.returncode != 0:
                        error_msg = stderr.decode('utf-8', errors='replace')
                        raise RuntimeError(f"Piper failed: {error_msg}")

                # Read the generated audio file
                with open(audio_filename, 'rb') as f:
                    audio_data = f.read()

                # Validate that we got a WAV file
                if len(audio_data) < 44:  # Minimum WAV header size
                    raise ValueError("Generated audio file is too small - likely not a valid WAV")

                self.logger.info(f"Synthesized {len(text)} characters to {len(audio_data)} bytes of audio using voice '{voice_name}'")
                return audio_data

            finally:
                # Clean up temporary files
                try:
                    os.unlink(text_filename)
                except:
                    pass
                try:
                    os.unlink(audio_filename)
                except:
                    pass

        except Exception as e:
            self.logger.error(f"Error synthesizing speech: {e}", exc_info=True)
            raise

    async def synthesize_to_file(
        self,
        text: str,
        output_path: str,
        voice: str = None,
        speed: float = 1.0
    ) -> bool:
        """
        Synthesize text to speech and save to a file

        Args:
            text: Text to synthesize
            output_path: Path to save the audio file
            voice: Voice name to use
            speed: Speech rate

        Returns:
            True if successful
        """
        try:
            audio_data = await self.synthesize(text, voice, speed)
            with open(output_path, 'wb') as f:
                f.write(audio_data)
            return True
        except Exception as e:
            self.logger.error(f"Error synthesizing to file {output_path}: {e}")
            return False

    async def get_available_voices(self) -> Dict[str, Any]:
        """Get information about available voices"""
        if not self.is_initialized:
            await self.initialize()

        # Return a simplified view of voices
        voice_info = {}
        for name, info in self.available_voices.items():
            voice_info[name] = {
                "name": name,
                "language": info["language"],
                "speaker_count": info["speaker_count"],
                "quality": "medium"  # Default - could be determined from model specs
            }

        return voice_info

    async def get_voice_details(self, voice_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific voice"""
        if not self.is_initialized:
            await self.initialize()

        if voice_name not in self.available_voices:
            raise ValueError(f"Voice '{voice_name}' not found")

        info = self.available_voices[voice_name]
        return {
            "name": info["name"],
            "language": info["language"],
            "speaker_count": info["speaker_count"],
            "model_path": info["model_path"],
            "config_path": info["config_path"],
            "sample_hertz": info["config"].get("audio", {}).get("sample_rate", 22050),
            "length_scale": info["config"].get("length_scale", 1.0)
        }

    async def is_voice_available(self, voice_name: str) -> bool:
        """Check if a voice is available"""
        if not self.is_initialized:
            await self.initialize()
        return voice_name in self.available_voices

    async def get_default_voice(self) -> str:
        """Get the default voice name"""
        if not self.is_initialized:
            await self.initialize()
        return self.default_voice

    async def set_default_voice(self, voice_name: str):
        """Set the default voice"""
        if not self.is_initialized:
            await self.initialize()
        if voice_name not in self.available_voices:
            raise ValueError(f"Voice '{voice_name}' not available")
        self.default_voice = voice_name
        self.logger.info(f"Default voice set to: {voice_name}")

    async def get_status(self) -> Dict[str, Any]:
        """Get status of the text-to-speech system"""
        return {
            "is_initialized": self.is_initialized,
            "executable_found": self.piper_path is not None,
            "default_voice": self.default_voice,
            "voices_count": len(self.available_voices),
            "available_voices": list(self.available_voices.keys()),
            "status": "ready" if self.is_initialized else "not_initialized"
        }

    async def shutdown(self):
        """Shutdown the Piper TTS"""
        self.logger.info("Shutting down Piper TTS")
        self.is_initialized = False