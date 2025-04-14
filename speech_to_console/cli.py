"""Command-line interface for Speech to Console."""

import asyncio
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.style import Style

from speech_to_console.audio import AudioRecorder
from speech_to_console.config import load_config
from speech_to_console.keyboard import KeyboardController
from speech_to_console.transcriber import TranscriptionProcessor, WhisperTranscriber

app = typer.Typer(
    name="speech-to-console",
    help="Convert spoken commands to console operations",
    add_completion=False,
)

console = Console()


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
        "Listening for activation phrase: 'hey stt'",
        style=Style(color="green", bold=True),
    )
    console.print(
        "Say 'end stt' or 'that's it for stt' to stop transcription",
        style=Style(color="green"),
    )

    is_active = False

    while True:
        try:
            # Record audio chunk (approx. 2-3 seconds)
            audio_data = audio_recorder.record_until_silence(
                max_seconds=3, silence_threshold=5
            )

            # Convert to bytes IO for API submission
            audio_bytes = audio_recorder.audio_to_bytes_io(audio_data)

            # Transcribe
            transcription = await transcriber.transcribe(audio_bytes)

            if not transcription:
                continue

            # Check for activation phrase
            if not is_active and processor.is_activation_phrase(transcription):
                is_active = True
                console.print(
                    "✅ Activated! Transcribing to active terminal...",
                    style=Style(color="green", bold=True),
                )

                # Extract command if it's in the same utterance
                command = processor.extract_command(transcription)
                if command:
                    console.print(f"🔤 Typing: {command}")
                    keyboard.type_text(command)

            # Process transcription when active
            elif is_active:
                # Check for deactivation phrase
                if processor.is_deactivation_phrase(transcription):
                    is_active = False
                    console.print(
                        "⛔ Deactivated. Listening for activation phrase...",
                        style=Style(color="red"),
                    )
                    continue

                # Type transcription (excluding control phrases)
                command = processor.extract_command(transcription)
                if not command:
                    command = transcription

                console.print(f"🔤 Typing: {command}")
                keyboard.type_text(command)

        except KeyboardInterrupt:
            break
        except Exception as e:
            console.print(f"Error: {e}", style=Style(color="red"))
            await asyncio.sleep(1)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show verbose output"),
) -> None:
    """Convert spoken commands to console operations."""
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

        # Initialize components
        audio_recorder = AudioRecorder()
        transcriber = WhisperTranscriber(config)
        processor = TranscriptionProcessor(config)
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

        # Run the main loop
        try:
            asyncio.run(process_audio(audio_recorder, transcriber, processor, keyboard))
        except KeyboardInterrupt:
            console.print("Exiting...", style=Style(color="yellow"))

    except Exception as e:
        console.print(f"Error: {e}", style=Style(color="red", bold=True))
        if verbose:
            import traceback

            console.print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    app()
