"""Configuration management for Speech to Console."""

import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Config(BaseModel):
    """Application configuration."""

    openai_api_key: str = Field(..., description="OpenAI API key")
    whisper_model: str = Field("whisper-1", description="Whisper model to use")
    api_timeout: int = Field(10, description="API request timeout in seconds")
    log_level: LogLevel = Field("INFO", description="Logging level")

    # Speech recognition settings
    activation_phrase: str = "okay, speechless"
    deactivation_phrases: list[str] = [
        "end speechless",
        "that's it for speechless",
        "stop speechless",
    ]

    # Audio settings
    silent_threshold: int = Field(
        100, description="Threshold for silence detection (lower = more sensitive)"
    )

    # Transcription filtering
    min_audio_duration_seconds: float = Field(
        0.5, description="Minimum audio duration in seconds to consider valid speech"
    )


def load_config() -> Config:
    """Load configuration from environment variables."""
    # Load from .env file
    env_path = Path(".env")
    load_dotenv(dotenv_path=env_path)

    # Get configuration values
    openai_api_key = os.getenv("OPENAI_API_KEY")
    whisper_model = os.getenv("WHISPER_MODEL", "whisper-1")
    api_timeout = int(os.getenv("API_TIMEOUT", "10"))
    log_level = os.getenv("LOG_LEVEL", "INFO")
    silent_threshold = int(os.getenv("SILENT_THRESHOLD", "50"))
    min_audio_duration_seconds = float(os.getenv("MIN_AUDIO_DURATION_SECONDS", "0.5"))

    if not openai_api_key:
        raise ValueError(
            "OPENAI_API_KEY not found in environment variables or .env file"
        )

    # Validate log level
    valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if log_level not in valid_log_levels:
        raise ValueError(
            f"Invalid LOG_LEVEL: {log_level}. "
            f"Must be one of: {', '.join(valid_log_levels)}"
        )

    return Config(
        openai_api_key=openai_api_key,
        whisper_model=whisper_model,
        api_timeout=api_timeout,
        log_level=log_level,
        silent_threshold=silent_threshold,
        min_audio_duration_seconds=min_audio_duration_seconds,
    )
