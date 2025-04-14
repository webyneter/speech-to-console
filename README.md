# Speech to Console

A tool that converts spoken commands to console/terminal operations using real-time speech recognition.

## Features

- Voice-activated command transcription for terminal
- Uses OpenAI Whisper API for accurate speech recognition
- Supports activation with "hey stt" and deactivation with "end stt" or "that's it for stt"
- Types transcribed text into active Ubuntu Terminal window

## Installation

### Basic Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/speech-to-console.git
cd speech-to-console

# Install with uv (runtime dependencies only)
uv sync

# Install with uv (including development dependencies)
uv sync --all-groups

# Or install with pip
pip install -e .
```

### Global Installation with pipx (Recommended)

For the best experience, install the tool globally using pipx:

```bash
# Install pipx if you don't have it
python -m pip install --user pipx
python -m pipx ensurepath

# Install speech-to-console globally
cd /path/to/speech-to-console
pipx install -e .
```

This makes the `speech-to-console` command available system-wide without affecting your global Python environment.

## Configuration

1. Create a `.env` file in the project root by copying `example.env`:

```bash
cp example.env .env
```

2. Add your OpenAI API key to the `.env` file:

```
OPENAI_API_KEY=your-api-key-here
```

## Usage

1. Open two terminal windows
2. In the first window, start the speech-to-console tool:

```bash
speech-to-console
```

3. In the second window, make it active (click on it)
4. Say "hey stt" to start transcription
5. Speak the commands you want typed into the terminal
6. Say "end stt" or "that's it for stt" to stop transcription

### How It Works

When you run the tool, it listens continuously for the activation phrase. Once detected:

1. The tool will indicate that it's activated and begin transcribing
2. Spoken words are sent to the OpenAI Whisper API for transcription
3. The transcribed text is typed into your active terminal window
4. When a deactivation phrase is detected, the tool returns to listening mode
5. Press Ctrl+C in the speech-to-console window to exit the program completely

## Development

```bash
# Install development dependencies
uv sync --all-groups

# Run tests
uv run pytest

# Run linting
uv run ruff check .

# Format code
uv run ruff format .
```

### Customization

You can customize the tool behavior by modifying these files:

- `speech_to_console/config.py`: Change activation/deactivation phrases 
- `speech_to_console/audio.py`: Adjust audio recording parameters
- `speech_to_console/keyboard.py`: Modify typing speed and behavior

### Troubleshooting

- **Microphone not working**: Check your system's audio input settings
- **API errors**: Verify your API key in the `.env` file
- **Text not being typed**: Make sure you've clicked on the target window
- **Transcription quality issues**: Try speaking more clearly or adjusting your microphone

## License

MIT
