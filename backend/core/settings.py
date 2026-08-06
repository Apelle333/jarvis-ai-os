"""
JARVIS AI Operating System - Settings Module
Handles configuration and environment variables
"""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Server Configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    debug: bool = Field(default=True, description="Debug mode")

    # Ollama Configuration
    ollama_host: str = Field(default="http://localhost:11434", description="Ollama server URL")
    ollama_timeout: int = Field(default=120, description="Ollama request timeout in seconds")

    # Model Configuration
    default_model: str = Field(default="qwen3:8b", description="Default model for general tasks")
    coder_model: str = Field(default="qwen2.5-coder:7b", description="Model for coding tasks")
    reasoning_model: str = Field(default="deepseek-r1:14b", description="Model for complex reasoning")

    # Explicit routing preferences (primary and fallback). These are used by ModelRouter.
    reasoning_primary: str = Field(default="deepseek-r1:14b")
    reasoning_fallback: str = Field(default="qwen3:8b")

    coding_primary: str = Field(default="qwen2.5-coder:7b")
    coding_fallback: str = Field(default="deepseek-r1:14b")

    general_primary: str = Field(default="qwen3:8b")
    general_fallback: str = Field(default="gemma4:12b")

    personality_primary: str = Field(default="gemma4:12b")
    personality_fallback: str = Field(default="qwen3:8b")

    fast_primary: str = Field(default="phi4-mini:latest")

    emergency_fallback: str = Field(default="qwen3:8b")

    last_resort_model: str = Field(default="gemma:7b")

    # Memory Configuration
    sqlite_db_path: str = Field(default="./database/jarvis_memory.db", description="SQLite database path")
    chroma_db_path: str = Field(default="./database/chroma_db", description="ChromaDB path")
    chroma_collection_name: str = Field(default="jarvis_knowledge", description="ChromaDB collection name")

    # Memory Settings
    short_term_memory_limit: int = Field(default=1000, description="Maximum short-term memory entries")
    long_term_memory_threshold: float = Field(default=0.7, description="Similarity threshold for long-term memory")
    memory_consolidation_interval: int = Field(default=3600, description="Memory consolidation interval in seconds")

    # Voice Settings
    speech_recognition_model: str = Field(default="base", description="Whisper model for speech recognition")
    tts_voice: str = Field(default="en_US-lessac-medium", description="Piper TTS voice")
    tts_speed: float = Field(default=1.0, description="Text-to-speech speed")
    tts_volume: float = Field(default=1.0, description="Text-to-speech volume")

    # System Settings
    max_concurrent_tasks: int = Field(default=5, description="Maximum concurrent tasks")
    task_timeout: int = Field(default=300, description="Task timeout in seconds")
    auto_save_interval: int = Field(default=300, description="Auto-save interval in seconds")

    # Security Settings
    enable_confirmation_prompts: bool = Field(default=True, description="Enable confirmation prompts for dangerous operations")
    allowed_commands: str = Field(default="ls,dir,cat,type,echo,mkdir,rmdir,copy,xcopy,del,erase,ren,rename", description="Comma-separated list of allowed commands")
    blocked_commands: str = Field(default="format,del *,erase *,rmdir /s,rd /s,shutdown,restart,del /f,erase /f", description="Comma-separated list of blocked commands")
    enable_api_security: bool = Field(default=False, description="Enable API token security for backend routes")
    api_security_token: Optional[str] = Field(default=None, description="Bearer token required for protected backend routes")
    cors_allowed_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001,http://tauri.localhost,tauri://localhost",
        description="Comma-separated list of allowed browser origins"
    )

    # Computer Control Settings
    computer_control_enabled: bool = Field(default=True, description="Enable computer control (app/window/input/file actions)")
    confirmation_threshold: str = Field(default="high", description="Minimum risk level that requires confirmation (low|medium|high|critical)")
    screenshot_dir: str = Field(default="./screenshots", description="Directory where JARVIS saves screenshots")
    workspace_root: str = Field(default="./workspace", description="Root directory for user-visible file operations")
    action_log_limit: int = Field(default=25, description="Number of recent actions kept for the HUD")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: str = Field(default="./logs/jarvis.log", description="Log file path")
    log_max_size: int = Field(default=10485760, description="Maximum log file size in bytes")
    log_backup_count: int = Field(default=5, description="Number of log backups to keep")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
