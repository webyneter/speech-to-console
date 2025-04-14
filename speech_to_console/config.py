"""Configuration management for Speech to Console."""

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field


class Config(BaseModel):
    """Application configuration."""

    openai_api_key: str = Field(..., description="OpenAI API key")
    whisper_model: str = Field("whisper-1", description="Whisper model to use")
    api_timeout: int = Field(10, description="API request timeout in seconds")

    # Speech recognition settings
    activation_phrase: str = "hey stt"
    deactivation_phrases: list[str] = ["end stt", "that's it for stt", "stop stt"]


def load_config() -> Config:
    """Load configuration from environment variables."""
    # Load from .env file
    env_path = Path(".env")
    load_dotenv(dotenv_path=env_path)

    # Get configuration values
    openai_api_key = os.getenv("OPENAI_API_KEY")
    whisper_model = os.getenv("WHISPER_MODEL", "whisper-1")
    api_timeout = int(os.getenv("API_TIMEOUT", "10"))

    if not openai_api_key:
        raise ValueError(
            "OPENAI_API_KEY not found in environment variables or .env file"
        )

    return Config(
        openai_api_key=openai_api_key,
        whisper_model=whisper_model,
        api_timeout=api_timeout,
    )
