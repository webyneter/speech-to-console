"""Transcription service using OpenAI's Whisper API."""

import io
from typing import Optional

import httpx

from speech_to_console.config import Config


class WhisperTranscriber:
    """Transcribes audio using OpenAI's Whisper API."""

    def __init__(self, config: Config):
        """Initialize the transcriber.

        Args:
            config: Application configuration
        """
        self.api_key = config.openai_api_key
        self.model = config.whisper_model
        self.timeout = config.api_timeout

        # API endpoint
        self.api_url = "https://api.openai.com/v1/audio/transcriptions"

    async def transcribe(self, audio_data: io.BytesIO) -> str:
        """Transcribe audio data using Whisper API.

        Args:
            audio_data: Audio data as BytesIO object

        Returns:
            Transcribed text

        Raises:
            Exception: If transcription fails
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        files = {
            "file": ("audio.wav", audio_data, "audio/wav"),
            "model": (None, self.model),
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.api_url,
                headers=headers,
                files=files,
            )

            if response.status_code != 200:
                raise Exception(f"Transcription failed: {response.text}")

            result = response.json()
            return result.get("text", "")


class TranscriptionProcessor:
    """Processes transcriptions and detects control phrases."""

    def __init__(self, config: Config):
        """Initialize the processor.

        Args:
            config: Application configuration
        """
        self.activation_phrase = config.activation_phrase.lower()
        self.deactivation_phrases = [p.lower() for p in config.deactivation_phrases]

    def is_activation_phrase(self, text: str) -> bool:
        """Check if text contains the activation phrase.

        Args:
            text: Transcribed text

        Returns:
            True if activation phrase is detected
        """
        return self.activation_phrase in text.lower()

    def is_deactivation_phrase(self, text: str) -> bool:
        """Check if text contains any deactivation phrase.

        Args:
            text: Transcribed text

        Returns:
            True if any deactivation phrase is detected
        """
        text_lower = text.lower()
        return any(phrase in text_lower for phrase in self.deactivation_phrases)

    def extract_command(self, text: str) -> Optional[str]:
        """Extract command from transcribed text.

        Args:
            text: Transcribed text

        Returns:
            Extracted command or None if no command found
        """
        text_lower = text.lower()

        # Check for activation phrase
        if self.activation_phrase in text_lower:
            # Extract text after activation phrase
            start_idx = text_lower.find(self.activation_phrase) + len(
                self.activation_phrase
            )
            command = text[start_idx:].strip()

            # Remove deactivation phrase if present
            for phrase in self.deactivation_phrases:
                if phrase in command.lower():
                    end_idx = command.lower().find(phrase)
                    command = command[:end_idx].strip()

            return command if command else None

        return None
