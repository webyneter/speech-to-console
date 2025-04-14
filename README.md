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
```

> **Note:** This project requires Python 3.10 specifically, not a newer version. This is due to compatibility issues with PyAutoGUI, a dependency used for keyboard input. As documented in [this PyAutoGUI issue](https://github.com/asweigart/pyautogui/issues/683#issuecomment-2750298345), the library has compatibility problems with Python 3.12+.

## Install the Package as a CLI

In addition to the basic installation, you will need the following system dependencies:

- [pipx](https://pypa.github.io/pipx/): A tool to install and run Python applications in isolated environments.
- System dependencies (for Ubuntu/Debian, run our install script):

```shell
# Run the dependency installation script (Ubuntu/Debian)
./install_dependencies.sh
```

Now, build the package:

```shell
uv build
```

Install the package:

```shell
uv run pipx install .
```

Check the installation:

```shell
speech-to-console --version
```

### Upgrade the Package

If you need to update the installed CLI tool after making changes:

```shell
# Build the package
uv build

# Option 1: Upgrade the installed package
uv run pipx upgrade speech-to-console

# Option 2: If you had a development install or significant changes
uv run pipx install --force .
```

Check the installation:

```shell
speech-to-console --version
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

# Optional: Change the logging level (default is INFO)
LOG_LEVEL=INFO
```

Available logging levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

## Usage

1. Open two terminal windows
2. In the first window, start the speech-to-console tool:

```bash
speech-to-console  # Basic usage

# For verbose logging (DEBUG level)
speech-to-console --verbose

# Set a specific logging level
speech-to-console --log-level DEBUG
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

- `speech_to_console/config.py`: Change activation/deactivation phrases and logging settings
- `speech_to_console/audio.py`: Adjust audio recording parameters
- `speech_to_console/keyboard.py`: Modify typing speed and behavior
- `speech_to_console/logging.py`: Customize logging configuration

### Troubleshooting

- **Microphone not working**: Check your system's audio input settings
- **API errors**: Verify your API key in the `.env` file
- **Text not being typed**: Make sure you've clicked on the target window
- **Transcription quality issues**: Try speaking more clearly or adjusting your microphone

## License

MIT
