# Speech to Console

A tool that converts spoken commands to console/terminal operations using real-time speech recognition.

## Features

- Voice-activated command transcription for terminal
- Uses OpenAI Whisper API for accurate speech recognition
- Supports activation with "okay, speechless" and deactivation with "end speechless" or "that's it for speechless"
- Types transcribed text into active Ubuntu Terminal window

## Installation

### Basic Installation

```bash
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

2. Add your OpenAI API key and customize settings in the `.env` file:

```
# Required: Your OpenAI API key
OPENAI_API_KEY=your-api-key-here

# Optional: Change the logging level (default is INFO)
LOG_LEVEL=INFO

# Optional: Adjust the microphone sensitivity (default is 100)
# Lower values = more sensitive (picks up quieter sounds)
# Higher values = less sensitive (requires louder speech)
# If you're getting false transcriptions from background noise, try 150-200
SILENT_THRESHOLD=100

# Optional: Minimum speech duration in seconds (default is 0.5)
# Increase this to filter out false transcriptions from background noise
# Try 0.7 or 1.0 if you're still getting false transcriptions
MIN_AUDIO_DURATION_SECONDS=0.5
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
4. Say "okay, speechless" to start transcription
5. Speak the commands you want typed into the terminal
6. Say "end speechless" or "that's it for speechless" to stop transcription

### How It Works

When you run the tool, it listens continuously for the activation phrase. Once detected:

1. The tool will indicate that it's activated and begin transcribing
2. Spoken words are sent to the OpenAI Whisper API for transcription
3. The transcribed text is typed into your active terminal window
4. When a deactivation phrase is detected, the tool returns to listening mode
5. The tool only processes commands between activation and deactivation phrases
6. Background noise and speech outside of active sessions are ignored
7. Press Ctrl+C in the speech-to-console window to exit the program completely

## Development

### Prerequisites

- Python 3.10 (required for PyAutoGUI compatibility)
- [uv](https://github.com/astral-sh/uv) package manager
- System dependencies (audio libraries, etc.) - can be installed with `./install_dependencies.sh`

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/speech-to-console.git
cd speech-to-console

# Sync dependencies (runtime only)
uv sync

# Sync all dependencies (including development)
uv sync --all-groups
```

### Running Locally

```bash
# Run directly from source
uv run speech-to-console

# Run with verbose logging
uv run speech-to-console --log-level DEBUG
```

### Testing and Code Quality

```bash
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
- **Text not being typed**: 
  - Make sure you've clicked on the target window before speaking
  - Check if PyAutoGUI has proper permissions on your system
  - Try running the app with elevated permissions if needed
  - If using Wayland, try switching to X11 (PyAutoGUI works better with X11)
  - The PyAutoGUI fail-safe has been disabled, so mouse movements won't interrupt typing
- **Activation phrase not detected**:
  - Run with `--log-level DEBUG` to see what the transcription actually heard
  - Try speaking "okay, speechless" more clearly and directly into the microphone
  - Try speaking in a quiet environment with minimal background noise
  - If you see your speech being transcribed but activation isn't happening, try adjusting the code in `transcriber.py` to add more variations of the activation phrase
- **Foreign characters or gibberish in transcription**:
  - This is a common issue with Whisper API when it's unsure of the language
  - We've updated the code to force English language detection
  - If you still see this issue, try speaking more clearly and avoid background noise
  - Keep speaking only English during usage
  - If the problem persists, try increasing the microphone volume
- **Background noise causing false transcriptions**:
  - If you're getting transcriptions when not speaking, increase the SILENT_THRESHOLD value
  - Adjust based on your environment noise levels:
    - For quiet environments: 100-150
    - For normal ambient noise: 200-300
    - For noisy environments: 400-500
  - Increase MIN_AUDIO_DURATION_SECONDS to filter out short noise bursts (try 0.7 or 1.0)
  - The app now uses advanced speech detection that analyzes both:
    - Amplitude (volume) of the sound
    - Variance in amplitude (human speech has high variance, constant noise doesn't)
  - Speech is only processed between activation and deactivation phrases
  - Background noise and speech outside the activation-deactivation cycle are ignored
  - Random words that appear during silence can be eliminated by increasing MIN_AUDIO_DURATION_SECONDS
  - Run with `--log-level DEBUG` to see detailed diagnostics about noise detection

## License

MIT
