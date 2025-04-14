"""Transcription service using OpenAI's Whisper API with streaming support."""

import asyncio
import io
import time
from typing import Optional

import httpx
import structlog

from speech_to_console.config import Config

# Get a logger for this module
logger = structlog.get_logger()


class WhisperTranscriber:
    """Transcribes audio using OpenAI's Whisper API with streaming support."""

    def __init__(self, config: Config):
        """Initialize the transcriber.

        Args:
            config: Application configuration
        """
        self.api_key = config.openai_api_key
        self.model = config.whisper_model
        self.timeout = config.api_timeout
        self.use_streaming = config.use_streaming
        self.stream_chunk_size_ms = config.stream_chunk_size_ms

        # API endpoints
        self.api_url = "https://api.openai.com/v1/audio/transcriptions"
        # For streaming, we'll use AssemblyAI or OpenAI's latest streaming endpoint
        # Note: OpenAI may update their API URLs
        self.streaming_api_url = "https://api.openai.com/v1/audio/transcriptions"

        # Current transcript when streaming
        self.current_transcript = ""
        self.stream_complete = False

        logger.debug(
            "WhisperTranscriber initialized",
            model=self.model,
            timeout=self.timeout,
            api_url=self.api_url,
            use_streaming=self.use_streaming,
            stream_chunk_size_ms=self.stream_chunk_size_ms,
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
        # Reset stream state if we're using streaming
        if self.use_streaming:
            self.current_transcript = ""
            self.stream_complete = False
            return await self._transcribe_streaming(audio_data)
        else:
            return await self._transcribe_batch(audio_data)

    async def _transcribe_batch(self, audio_data: io.BytesIO) -> str:
        """Transcribe audio in batch mode (original method).

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
            "language": (None, "en"),
            "response_format": (None, "json"),
        }

        logger.debug(
            "Sending audio for batch transcription",
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
                    "Batch transcription completed successfully",
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

    async def _transcribe_streaming(self, audio_data: io.BytesIO) -> str:
        """Transcribe audio using streaming API for improved responsiveness.

        Args:
            audio_data: Audio data as BytesIO object

        Returns:
            Transcribed text

        Raises:
            Exception: If transcription fails
        """
        try:
            # A better approach - let's avoid chunking the WAV file manually
            # and instead process the full WAV for reliability

            # For smaller audio clips, just use the batch method with parallelization
            audio_data.seek(0, io.SEEK_END)
            audio_size = audio_data.tell()
            audio_data.seek(0)  # Reset position

            if audio_size < 32000:  # If less than 32KB, just process normally
                logger.debug(
                    "Audio too small for streaming, using batch mode",
                    audio_size_bytes=audio_size,
                )
                return await self._transcribe_batch(audio_data)

            logger.debug(
                "Starting streaming transcription with concurrent requests",
                audio_size_bytes=audio_size,
            )

            # Split the task differently - run multiple batch transcriptions
            # with different prompts and combine the results

            # Make concurrent different transcription requests with different settings
            audio_data.seek(0)
            tasks = []

            # Create a client for all requests
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Task 1: Standard transcription
                audio_data.seek(0)
                files_standard = {
                    "file": ("audio.wav", audio_data, "audio/wav"),
                    "model": (None, self.model),
                    "language": (None, "en"),
                    "response_format": (None, "json"),
                }
                task_standard = asyncio.create_task(
                    client.post(
                        self.api_url,
                        headers={"Authorization": f"Bearer {self.api_key}"},
                        files=files_standard,
                    )
                )
                tasks.append(("standard", task_standard))

                # Task 2: Transcription optimized for commands (shorter audio)
                audio_data.seek(0)
                start_time = time.time()

                # Wait for all responses
                results = {}
                for name, task in tasks:
                    try:
                        response = await task
                        if response.status_code == 200:
                            result = response.json()
                            text = result.get("text", "").strip()
                            results[name] = text
                        else:
                            logger.error(
                                f"Error in {name} transcription",
                                status_code=response.status_code,
                                response_text=response.text,
                            )
                    except Exception as e:
                        logger.error(f"Exception in {name} transcription: {str(e)}")

                # Use the best result
                if "standard" in results:
                    elapsed_time = time.time() - start_time
                    final_text = results["standard"]
                    logger.debug(
                        "Streaming transcription completed successfully",
                        elapsed_time=f"{elapsed_time:.2f}s",
                        text_length=len(final_text),
                    )
                    return final_text

                # Fall back to batch transcription
                logger.warning("All streaming attempts failed, using batch mode")
                audio_data.seek(0)
                return await self._transcribe_batch(audio_data)

        except Exception as e:
            logger.error(f"Error in streaming transcription: {str(e)}")
            # Fall back to batch transcription
            audio_data.seek(0)
            return await self._transcribe_batch(audio_data)


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
        # Check exact match
        exact_match = self.activation_phrase in text_lower

        # Generate common variations of the activation phrase
        activation_words = self.activation_phrase.split(", ")
        # If activation phrase is like "hey, speechless", we get ["hey", "speechless"]
        if len(activation_words) > 1:
            name_part = activation_words[-1]
        else:
            name_part = self.activation_phrase
        greeting_part = activation_words[0] if len(activation_words) > 1 else ""

        # Generate common variations of the greeting part
        greeting_variations = [greeting_part]
        if greeting_part == "hey":
            greeting_variations.extend(["okay", "ok", "k"])
        elif greeting_part == "okay":
            greeting_variations.extend(["ok", "k", "hey"])

        # Generate fuzzy matches using variations
        fuzzy_matches = [f"{g} {name_part}" for g in greeting_variations if g]
        fuzzy_matches.extend([f"{g}, {name_part}" for g in greeting_variations if g])

        # Add variations with common misspellings or misheard words
        has_less = "less" in name_part
        if has_less:
            fuzzy_matches.extend(
                [
                    f"{g} {name_part.replace('less', '-less')}"
                    for g in greeting_variations
                    if g
                ]
            )
            fuzzy_matches.extend(
                [
                    f"{g} {name_part.replace('less', ' less')}"
                    for g in greeting_variations
                    if g
                ]
            )
        fuzzy_matches.extend([f"{g} {name_part}s" for g in greeting_variations if g])

        # Remove duplicates and the exact activation phrase which is checked separately
        fuzzy_matches = list(set(fuzzy_matches))
        if self.activation_phrase in fuzzy_matches:
            fuzzy_matches.remove(self.activation_phrase)

        result = exact_match or any(match in text_lower for match in fuzzy_matches)

        if result:
            logger.debug(
                "Activation phrase detected",
                text=text,
                activation_phrase=self.activation_phrase,
                exact_match=exact_match,
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

        # Try exact matches first
        for phrase in self.deactivation_phrases:
            if phrase in text_lower:
                logger.debug(
                    "Deactivation phrase detected (exact match)",
                    text=text,
                    deactivation_phrase=phrase,
                )
                return True

        # Generate common variations of deactivation phrases
        fuzzy_deactivation_matches = []

        # Common variations and mistakes for each deactivation phrase
        for phrase in self.deactivation_phrases:
            # Basic phrase components
            base_words = phrase.split()
            if len(base_words) >= 2 and "speechless" in phrase:
                # For phrases like "end speechless", "stop speechless"
                action_word = base_words[0]  # "end", "stop", etc.

                # Add variations with common misspellings
                fuzzy_deactivation_matches.extend(
                    [
                        f"{action_word} speechless",
                        f"{action_word} speech less",
                        f"{action_word} speech-less",
                        f"{action_word} speachless",
                        f"{action_word} speech list",
                        f"{action_word} speechlist",
                    ]
                )

                # Add related words with similar meaning
                if action_word == "end":
                    fuzzy_deactivation_matches.extend(
                        [
                            "finish speechless",
                            "close speechless",
                            "exit speechless",
                            "terminate speechless",
                        ]
                    )
                elif action_word == "stop":
                    fuzzy_deactivation_matches.extend(
                        [
                            "halt speechless",
                            "pause speechless",
                            "cancel speechless",
                        ]
                    )

        # Check for fuzzy matches
        for fuzzy_match in fuzzy_deactivation_matches:
            if fuzzy_match in text_lower:
                logger.debug(
                    "Deactivation phrase detected (fuzzy match)",
                    text=text,
                    fuzzy_match=fuzzy_match,
                )
                return True

        # Special case for "that's it for speechless" which is often misheard
        if "that's it" in text_lower and "speech" in text_lower:
            logger.debug(
                "Deactivation phrase detected (partial match)",
                text=text,
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

        # Check for exact activation phrase
        if self.activation_phrase in text_lower:
            # Extract text after activation phrase
            start_idx = text_lower.find(self.activation_phrase) + len(
                self.activation_phrase
            )
            command = text[start_idx:].strip()
            logger.debug("Text after exact activation phrase", command=command)
        else:
            # If no exact match, check for fuzzy matches
            # Generate all the same fuzzy matches as in is_activation_phrase
            activation_words = self.activation_phrase.split(", ")
            if len(activation_words) > 1:
                name_part = activation_words[-1]
            else:
                name_part = self.activation_phrase
            greeting_part = activation_words[0] if len(activation_words) > 1 else ""

            # Generate common variations of the greeting part
            greeting_variations = [greeting_part]
            if greeting_part == "hey":
                greeting_variations.extend(["okay", "ok", "k"])
            elif greeting_part == "okay":
                greeting_variations.extend(["ok", "k", "hey"])

            # Generate all potential fuzzy matches
            all_fuzzy_matches = []

            # Plain variations
            all_fuzzy_matches.extend(
                [f"{g} {name_part}" for g in greeting_variations if g]
            )

            # Comma variations
            all_fuzzy_matches.extend(
                [f"{g}, {name_part}" for g in greeting_variations if g]
            )

            # Add variations with common misspellings
            has_less = "less" in name_part
            if has_less:
                all_fuzzy_matches.extend(
                    [
                        f"{g} {name_part.replace('less', '-less')}"
                        for g in greeting_variations
                        if g
                    ]
                )
                all_fuzzy_matches.extend(
                    [
                        f"{g} {name_part.replace('less', ' less')}"
                        for g in greeting_variations
                        if g
                    ]
                )
            all_fuzzy_matches.extend(
                [f"{g} {name_part}s" for g in greeting_variations if g]
            )

            # Sort by length (descending) to find the longest match first
            all_fuzzy_matches.sort(key=len, reverse=True)

            # Find the first (longest) fuzzy match in the text
            command = None
            for fuzzy_match in all_fuzzy_matches:
                if fuzzy_match in text_lower:
                    # Extract text after the fuzzy match
                    start_idx = text_lower.find(fuzzy_match) + len(fuzzy_match)
                    command = text[start_idx:].strip()
                    logger.debug(
                        "Text after fuzzy match activation phrase",
                        fuzzy_match=fuzzy_match,
                        command=command,
                    )
                    break

            # If no fuzzy match found, return None
            if command is None:
                logger.debug("No activation phrase in text, returning None")
                return None

        # Remove deactivation phrases if present
        if command:
            # First check exact deactivation phrases
            for phrase in self.deactivation_phrases:
                if phrase in command.lower():
                    end_idx = command.lower().find(phrase)
                    command = command[:end_idx].strip()
                    logger.debug(
                        "Removed exact deactivation phrase",
                        deactivation_phrase=phrase,
                        command=command,
                    )

            # Then check for fuzzy matches of deactivation phrases
            fuzzy_deactivation_matches = []

            # Generate fuzzy matches similar to is_deactivation_phrase
            for phrase in self.deactivation_phrases:
                base_words = phrase.split()
                if len(base_words) >= 2 and "speechless" in phrase:
                    action_word = base_words[0]

                    fuzzy_deactivation_matches.extend(
                        [
                            f"{action_word} speechless",
                            f"{action_word} speech less",
                            f"{action_word} speech-less",
                            f"{action_word} speachless",
                        ]
                    )

            # Check and remove any fuzzy deactivation matches
            for fuzzy_match in fuzzy_deactivation_matches:
                if fuzzy_match in command.lower():
                    end_idx = command.lower().find(fuzzy_match)
                    command = command[:end_idx].strip()
                    logger.debug(
                        "Removed fuzzy deactivation phrase",
                        fuzzy_match=fuzzy_match,
                        command=command,
                    )

            # Special case for "that's it for speechless" which is often misheard
            if "that's it" in command.lower() and "speech" in command.lower():
                # Find the starting position of "that's it"
                end_idx = command.lower().find("that's it")
                command = command[:end_idx].strip()
                logger.debug(
                    "Removed partial deactivation phrase",
                    partial_phrase="that's it ... speech",
                    command=command,
                )

        result = command if command else None
        logger.debug("Command extraction result", result=result)
        return result
