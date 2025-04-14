# Speech to Console

A tool that converts spoken commands to console/terminal operations using real-time speech recognition.

## Features

- Voice-activated command transcription for terminal
- Uses OpenAI Whisper API for accurate speech recognition
- Supports activation with "hey stt" and deactivation with "end stt" or "that's it for stt"
- Types transcribed text into active Ubuntu Terminal window

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/speech-to-console.git
cd speech-to-console

# Install with uv
uv sync

# Or install with pip
pip install -e .
```

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

## Development

```bash
# Install development dependencies
uv sync

# Run tests
pytest

# Run linting
ruff check .

# Format code
ruff format .
```

## License

MIT
