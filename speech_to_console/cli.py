"""Command-line interface for Speech to Console."""

import asyncio
import sys
from pathlib import Path

import numpy as np
import structlog
import typer
from rich.console import Console
from rich.style import Style

from speech_to_console.audio import AudioRecorder
from speech_to_console.config import load_config
from speech_to_console.keyboard import KeyboardController
from speech_to_console.logging import setup_logging
from speech_to_console.transcriber import TranscriptionProcessor, WhisperTranscriber

app = typer.Typer(
    name="speech-to-console",
    help="Convert spoken commands to console operations",
    add_completion=False,
)

console = Console()
logger = structlog.get_logger("speech_to_console")


async def process_audio(
    audio_recorder: AudioRecorder,
    transcriber: WhisperTranscriber,
    processor: TranscriptionProcessor,
    keyboard: KeyboardController,
) -> None:
    """Process audio input continuously.

    Args:
        audio_recorder: Audio recorder instance
        transcriber: Whisper transcriber instance
        processor: Transcription processor instance
        keyboard: Keyboard controller instance
    """
    console.print(
        "Listening for activation phrase: 'okay, speechless'",
        style=Style(color="green", bold=True),
    )
    console.print(
        "Say 'end speechless' or 'that's it for speechless' to stop transcription",
        style=Style(color="green"),
    )

    logger.info(
        "Audio processing started",
        activation_phrase=processor.activation_phrase,
        deactivation_phrases=processor.deactivation_phrases,
    )

    is_active = False
    in_valid_cycle = (
        False  # Flag to track if we're in a valid activation-deactivation cycle
    )

    while True:
        try:
            # Record audio chunk (approx. 2-3 seconds)
            logger.debug("Recording audio chunk", max_seconds=3, silence_threshold=5)
            audio_data = audio_recorder.record_until_silence(
                max_seconds=3, silence_threshold=5
            )

            # Skip processing if audio data is all zeros (background noise)
            if np.all(audio_data == 0):
                logger.debug("Skipping empty audio (background noise)")
                await asyncio.sleep(0.1)  # Short sleep to avoid CPU spinning
                continue

            # Get speech duration from the recorder's metadata dictionary
            speech_duration = audio_recorder.last_recording_metadata.get(
                "active_speech_duration", 0.0
            )

            # Skip processing if speech duration is too short (non-active state only)
            if (
                not is_active
                and speech_duration < audio_recorder.min_audio_duration_seconds
            ):
                logger.debug(
                    "Skipping audio with insufficient speech duration",
                    speech_duration=f"{speech_duration:.3f}s",
                    required_duration=f"{audio_recorder.min_audio_duration_seconds:.3f}s",
                )
                await asyncio.sleep(0.1)
                continue

            # Convert to bytes IO for API submission
            audio_bytes = audio_recorder.audio_to_bytes_io(audio_data)
            logger.debug(
                "Audio recorded and converted", audio_length_samples=len(audio_data)
            )

            # Always process for activation phrase detection
            logger.debug(
                "Transcribing audio for control phrase detection",
                model=transcriber.model,
            )
            transcription = await transcriber.transcribe(audio_bytes)

            if not transcription:
                logger.debug("Empty transcription received, continuing")
                continue

            logger.debug(
                "Transcription received",
                raw_text=transcription,
                is_active=is_active,
                in_valid_cycle=in_valid_cycle,
            )

            # Check for activation phrase - always do this
            if not is_active and processor.is_activation_phrase(transcription):
                is_active = True
                in_valid_cycle = True  # Start of a valid cycle
                logger.info(
                    "Activation phrase detected",
                    transcription=transcription,
                    cycle_started=True,
                )
                # Truncate transcription if too long
                max_len = 35
                detected_in = transcription
                if len(detected_in) > max_len:
                    detected_in = detected_in[:max_len] + "..."
                msg = f"✅ Activated! Transcribing to terminal... ('{detected_in}')"
                console.print(
                    msg,
                    style=Style(color="green", bold=True),
                )

                # Extract command if it's in the same utterance
                command = processor.extract_command(transcription)
                if command:
                    logger.info(
                        "Command extracted from activation utterance", command=command
                    )
                    console.print(f"🔤 Typing: {command}")
                    keyboard.type_text(command)
                continue

            # If not in a valid cycle, show what was heard but don't process further
            if not in_valid_cycle:
                # Only show occasional feedback when listening for activation
                if not is_active:
                    console.print(
                        f"👂 Listening... (Heard: '{transcription}')",
                        style=Style(color="blue", dim=True),
                    )
                continue

            # Process transcription when active
            if is_active:
                # Check for deactivation phrase
                if processor.is_deactivation_phrase(transcription):
                    is_active = False
                    in_valid_cycle = False  # End of valid cycle
                    logger.info(
                        "Deactivation phrase detected",
                        transcription=transcription,
                        cycle_ended=True,
                    )
                    console.print(
                        "⛔ Deactivated. Listening for activation phrase...",
                        style=Style(color="red"),
                    )
                    continue

                # Type transcription (excluding control phrases)
                command = processor.extract_command(transcription)
                if not command:
                    command = transcription

                logger.info("Typing command", command=command)
                console.print(f"🔤 Typing: {command}")
                keyboard.type_text(command)

        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, stopping")
            break
        except Exception as e:
            logger.error("Error during audio processing", error=str(e), exc_info=True)
            console.print(f"Error: {e}", style=Style(color="red"))
            await asyncio.sleep(1)


def version_callback(value: bool) -> None:
    """Show the version and exit."""
    if value:
        from speech_to_console import __version__

        print(f"speech-to-console version: {__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show verbose output"),
    version: bool = typer.Option(False, "--version", help="Show the version and exit."),
    log_level: str = typer.Option(
        None,
        "--log-level",
        help="Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    ),
) -> None:
    """Convert spoken commands to console operations."""
    if version:
        version_callback(version)

    if ctx.invoked_subcommand is not None:
        return

    # Ensure .env file exists
    env_path = Path(".env")
    example_env_path = Path("example.env")

    if not env_path.exists() and example_env_path.exists():
        console.print(
            "⚠️ [yellow].env file not found. Copy example.env to .env first.[/yellow]"
        )
        sys.exit(1)

    try:
        # Load configuration
        config = load_config()

        # Override log level from command line if provided
        if log_level:
            config.log_level = log_level

        # Force DEBUG level if verbose flag is used
        if verbose:
            config.log_level = "DEBUG"  # type: ignore # Mypy flags this, but it's valid at runtime

        # Setup logging
        global logger
        logger = setup_logging(config)

        logger.info(
            "Speech to Console starting",
            version=getattr(sys.modules["speech_to_console"], "__version__", "unknown"),
            log_level=config.log_level,
            whisper_model=config.whisper_model,
        )

        # Initialize components
        logger.debug(
            "Initializing audio recorder",
            silent_threshold=config.silent_threshold,
            min_audio_duration_seconds=config.min_audio_duration_seconds,
        )
        audio_recorder = AudioRecorder(
            silent_threshold=config.silent_threshold,
            min_audio_duration_seconds=config.min_audio_duration_seconds,
        )

        logger.debug("Initializing transcriber", model=config.whisper_model)
        transcriber = WhisperTranscriber(config)

        logger.debug(
            "Initializing transcription processor",
            activation_phrase=config.activation_phrase,
            deactivation_phrases=config.deactivation_phrases,
        )
        processor = TranscriptionProcessor(config)

        logger.debug("Initializing keyboard controller")
        keyboard = KeyboardController()

        # Start processing
        console.print(
            "🎤 Speech to Console started",
            style=Style(color="blue", bold=True),
        )
        console.print(
            "Press Ctrl+C to exit",
            style=Style(color="yellow"),
        )

        logger.info("Audio processing loop starting")

        # Run the main loop
        try:
            asyncio.run(process_audio(audio_recorder, transcriber, processor, keyboard))
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, exiting")
            console.print("Exiting...", style=Style(color="yellow"))

    except Exception as e:
        error_msg = str(e)
        logger.error("Startup error", error=error_msg, exc_info=True)
        console.print(f"Error: {error_msg}", style=Style(color="red", bold=True))
        if verbose:
            import traceback

            console.print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    app()
