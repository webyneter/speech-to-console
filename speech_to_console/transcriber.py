"""Transcription service using OpenAI's Whisper API."""

import io
import time
from typing import Optional

import httpx
import structlog

from speech_to_console.config import Config

# Get a logger for this module
logger = structlog.get_logger()


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

        logger.debug(
            "WhisperTranscriber initialized",
            model=self.model,
            timeout=self.timeout,
            api_url=self.api_url,
        )

    async def transcribe(self, audio_data: io.BytesIO) -> str:
        """Transcribe audio data using Whisper API.

        Args:
            audio_data: Audio data as BytesIO object

        Returns:
            Transcribed text

        Raises:
            Exception: If transcription fails
        """
        # Get current position to determine size
        audio_data.seek(0, io.SEEK_END)
        audio_size = audio_data.tell()
        audio_data.seek(0)  # Reset position

        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        files = {
            "file": ("audio.wav", audio_data, "audio/wav"),
            "model": (None, self.model),
        }

        logger.debug(
            "Sending audio for transcription",
            audio_size_bytes=audio_size,
            api_url=self.api_url,
            model=self.model,
        )

        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    files=files,
                )

                elapsed_time = time.time() - start_time
                logger.debug(
                    "Received API response",
                    status_code=response.status_code,
                    elapsed_time=f"{elapsed_time:.2f}s",
                )

                if response.status_code != 200:
                    logger.error(
                        "Transcription API error",
                        status_code=response.status_code,
                        response_text=response.text,
                    )
                    raise Exception(f"Transcription failed: {response.text}")

                result = response.json()
                transcription = result.get("text", "")
                logger.debug(
                    "Transcription completed successfully",
                    text_length=len(transcription),
                )
                return transcription

        except httpx.TimeoutException as err:
            logger.error("Transcription API timeout", timeout=self.timeout)
            msg = f"Transcription API timed out after {self.timeout} seconds"
            raise Exception(msg) from err
        except Exception as e:
            logger.error("Transcription error", error=str(e), exc_info=True)
            raise


class TranscriptionProcessor:
    """Processes transcriptions and detects control phrases."""

    def __init__(self, config: Config):
        """Initialize the processor.

        Args:
            config: Application configuration
        """
        self.activation_phrase = config.activation_phrase.lower()
        self.deactivation_phrases = [p.lower() for p in config.deactivation_phrases]

        logger.debug(
            "TranscriptionProcessor initialized",
            activation_phrase=self.activation_phrase,
            deactivation_phrases=self.deactivation_phrases,
        )

    def is_activation_phrase(self, text: str) -> bool:
        """Check if text contains the activation phrase.

        Args:
            text: Transcribed text

        Returns:
            True if activation phrase is detected
        """
        text_lower = text.lower()
        result = self.activation_phrase in text_lower

        if result:
            logger.debug(
                "Activation phrase detected",
                text=text,
                activation_phrase=self.activation_phrase,
            )

        return result

    def is_deactivation_phrase(self, text: str) -> bool:
        """Check if text contains any deactivation phrase.

        Args:
            text: Transcribed text

        Returns:
            True if any deactivation phrase is detected
        """
        text_lower = text.lower()

        for phrase in self.deactivation_phrases:
            if phrase in text_lower:
                logger.debug(
                    "Deactivation phrase detected",
                    text=text,
                    deactivation_phrase=phrase,
                )
                return True

        return False

    def extract_command(self, text: str) -> Optional[str]:
        """Extract command from transcribed text.

        Args:
            text: Transcribed text

        Returns:
            Extracted command or None if no command found
        """
        text_lower = text.lower()
        logger.debug("Extracting command from text", text=text)

        # Check for activation phrase
        if self.activation_phrase in text_lower:
            # Extract text after activation phrase
            start_idx = text_lower.find(self.activation_phrase) + len(
                self.activation_phrase
            )
            command = text[start_idx:].strip()
            logger.debug("Text after activation phrase", command=command)

            # Remove deactivation phrase if present
            for phrase in self.deactivation_phrases:
                if phrase in command.lower():
                    end_idx = command.lower().find(phrase)
                    command = command[:end_idx].strip()
                    logger.debug(
                        "Removed deactivation phrase",
                        deactivation_phrase=phrase,
                        command=command,
                    )

            result = command if command else None
            logger.debug("Command extraction result", result=result)
            return result

        logger.debug("No activation phrase in text, returning None")
        return None
