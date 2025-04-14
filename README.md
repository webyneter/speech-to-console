# Speech to Console

A voice-controlled tool that converts spoken commands to text in your terminal using OpenAI's Whisper API.

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Requirements](#-requirements)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Troubleshooting](#-troubleshooting)
- [Development](#-development)
- [License](#-license)

## 🔍 Overview

Speech to Console lets you control your terminal with voice commands. Just say "hey, speechless" to activate, speak your commands, and say "end speechless" when you're done. The tool transcribes your speech and types it directly into your terminal.

## ✨ Key Features

- **Voice-activated command transcription** for terminals and consoles
- **Accurate speech recognition** using OpenAI's Whisper API
- **Real-time streaming transcription** for improved responsiveness
- **Intelligent noise filtering** that distinguishes human speech from background noise
- **Simple activation/deactivation** with customizable phrases
- **Adapts to different environments** with adjustable audio sensitivity
- **Parallel processing** of audio chunks for faster results

## 🧰 Requirements

- Python 3.10 (specifically required due to PyAutoGUI compatibility)
- OpenAI API key
- Linux-based system (tested on Ubuntu)
- Audio input device (microphone)

## 📦 Installation

### Quick Install

```bash
# 1. Clone and enter the repository
git clone https://github.com/webyneter/speech-to-console.git
cd speech-to-console

# 2. Install system dependencies (Ubuntu/Debian)
./install_dependencies.sh

# 3. Install Python dependencies
uv sync

# 4. Create configuration file
cp example.env .env
# Edit .env to add your OpenAI API key
```

### Install as CLI Tool

To make the command available system-wide:

```bash
# Build and install using pipx
uv build
uv run pipx install .

# Verify installation
speech-to-console --version
```

### Updating the CLI Tool

After making changes:

```bash
uv build
uv run pipx upgrade speech-to-console
# Or for significant changes:
uv run pipx install --force .
```

## ⚙️ Configuration

Edit your `.env` file with the following settings:

```env
# Required: Your OpenAI API key
OPENAI_API_KEY=your-api-key-here

# Optional settings with defaults shown:
LOG_LEVEL=INFO                    # Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
SILENT_THRESHOLD=400              # Microphone sensitivity (lower = more sensitive)
MIN_AUDIO_DURATION_SECONDS=0.5    # Minimum audio duration to process
USE_STREAMING=true                # Use streaming for more responsive transcription
STREAM_CHUNK_SIZE_MS=500          # Size of audio chunks for streaming (milliseconds)
```

### Audio Sensitivity Settings

| Environment      | Recommended SILENT_THRESHOLD |
|------------------|------------------------------|
| Quiet            | 100-150                      |
| Normal ambient   | 200-300                      |
| Noisy            | 400-500                      |

## 🚀 Usage

### Basic Operation

1. Start the tool in one terminal:
   ```bash
   speech-to-console
   # Or with debug logging:
   speech-to-console --verbose
   ```

2. Click on your target terminal window where you want text typed

3. Voice commands:
   - Say **"hey, speechless"** to activate (default activation phrase)
   - Speak your commands
   - Say **"end speechless"** to deactivate (default deactivation phrase)

### How It Works

1. **Listening Phase**: Monitors for activation phrase with noise filtering
2. **Active Phase**: Transcribes all speech until deactivation phrase is detected
3. **Typing Phase**: Converts speech to text and types it into the active window

### Streaming Transcription

Speech to Console uses a parallel streaming approach that:

1. Divides audio into small chunks (configurable, default 500ms)
2. Processes these chunks in parallel to reduce overall latency
3. Combines chunk results intelligently to create a smooth transcription
4. Falls back to regular batch processing if streaming encounters issues

You can adjust streaming settings in your `.env` file:
```env
USE_STREAMING=true                # Enable/disable streaming (true/false)
STREAM_CHUNK_SIZE_MS=500          # Chunk size in milliseconds (smaller = faster response)
```

## 🔧 Troubleshooting

### Common Issues

#### Microphone Problems
- Verify your microphone is working and properly configured in system settings
- Test with `arecord -d 5 test.wav && aplay test.wav` to confirm audio recording works

#### Activation Phrase Not Detected
- Speak clearly and directly into the microphone
- Run with `--log-level DEBUG` to see what's being transcribed
- Try adjusting environment variables in `.env`

#### False Transcriptions
- Increase `SILENT_THRESHOLD` (try 300-500 for noisy environments)
- Increase `MIN_AUDIO_DURATION_SECONDS` to 0.7 or 1.0
- Ensure you're in a reasonably quiet environment

#### Text Not Being Typed
- Ensure the target window is active
- If using Wayland, try switching to X11 (PyAutoGUI works better with X11)
- Run with `--verbose` flag to see detailed logs

## 💻 Development

### Setup Development Environment

```bash
# Install all dependencies including development tools
uv sync --all-groups
```

### Testing and Linting

```bash
# Run tests
uv run pytest

# Run linting
uv run ruff check .

# Auto-fix formatting issues
uv run ruff check --fix .
```

### Project Structure

```
speech-to-console/
├── speech_to_console/     # Core package code
│   ├── __init__.py        # Package initialization
│   ├── audio.py           # Audio recording functionality
│   ├── cli.py             # Command-line interface
│   ├── config.py          # Configuration management
│   ├── keyboard.py        # Keyboard control functions
│   ├── logging.py         # Logging configuration
│   └── transcriber.py     # Speech transcription with Whisper API
├── tests/                 # Unit tests
├── example.env            # Example environment file
└── install_dependencies.sh # System dependency installer
```

### Customization

You can modify the behavior by editing:

- `config.py` - Change activation/deactivation phrases
- `audio.py` - Adjust audio recording parameters
- `transcriber.py` - Modify how speech is processed

## 📄 License

MIT
