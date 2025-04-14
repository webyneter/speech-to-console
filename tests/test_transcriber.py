"""Tests for the transcriber module."""

import io
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from speech_to_console.config import Config
from speech_to_console.transcriber import TranscriptionProcessor, WhisperTranscriber


def test_activation_phrase_detection():
    """Test detection of activation phrase."""
    config = Config(
        openai_api_key="fake_key",
        activation_phrase="hey stt",
        deactivation_phrases=["end stt", "that's it for stt"],
    )
    processor = TranscriptionProcessor(config)

    # Test exact match
    assert processor.is_activation_phrase("hey stt")

    # Test in sentence
    assert processor.is_activation_phrase("I said hey stt and then more")

    # Test case insensitivity
    assert processor.is_activation_phrase("Hey STT")

    # Test non-match
    assert not processor.is_activation_phrase("hey st")
    assert not processor.is_activation_phrase("start recording")


def test_deactivation_phrase_detection():
    """Test detection of deactivation phrases."""
    config = Config(
        openai_api_key="fake_key",
        activation_phrase="hey stt",
        deactivation_phrases=["end stt", "that's it for stt"],
    )
    processor = TranscriptionProcessor(config)

    # Test exact matches
    assert processor.is_deactivation_phrase("end stt")
    assert processor.is_deactivation_phrase("that's it for stt")

    # Test in sentences
    assert processor.is_deactivation_phrase("I said end stt now")
    assert processor.is_deactivation_phrase("and that's it for stt thank you")

    # Test case insensitivity
    assert processor.is_deactivation_phrase("END STT")
    assert processor.is_deactivation_phrase("That's IT for STT")

    # Test non-match
    assert not processor.is_deactivation_phrase("end command")
    assert not processor.is_deactivation_phrase("start stt")


def test_command_extraction():
    """Test extraction of commands from transcriptions."""
    config = Config(
        openai_api_key="fake_key",
        activation_phrase="hey stt",
        deactivation_phrases=["end stt", "that's it for stt"],
    )
    processor = TranscriptionProcessor(config)

    # Test simple extraction
    assert processor.extract_command("hey stt ls -la") == "ls -la"

    # Test with deactivation phrase
    assert (
        processor.extract_command("hey stt echo hello world end stt")
        == "echo hello world"
    )

    # Test with mixed case
    assert processor.extract_command("Hey STT cd /home That's it for STT") == "cd /home"

    # Test no activation phrase
    assert processor.extract_command("ls -la") is None

    # Test only activation phrase
    assert processor.extract_command("hey stt") is None

    # Test activation followed immediately by deactivation
    assert processor.extract_command("hey stt end stt") is None


@pytest.fixture
def whisper_transcriber():
    """Create a test transcriber instance."""
    config = Config(
        openai_api_key="fake_api_key",
        whisper_model="whisper-1",
        api_timeout=10,
    )
    return WhisperTranscriber(config)


@pytest.mark.asyncio
async def test_transcribe_success(whisper_transcriber):
    """Test successful audio transcription."""
    # Create a mock audio BytesIO object
    mock_audio = io.BytesIO(b"mock audio data")

    # Create a mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"text": "hello world"}

    # Create a mock client that returns our mock response
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value.post.return_value = mock_response

    # Patch the httpx.AsyncClient to return our mock
    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await whisper_transcriber.transcribe(mock_audio)

        # Verify the result
        assert result == "hello world"

        # Verify the API was called correctly
        mock_client.__aenter__.return_value.post.assert_called_once()

        # Get the call arguments
        args, kwargs = mock_client.__aenter__.return_value.post.call_args

        # Check the URL
        assert args[0] == whisper_transcriber.api_url

        # Check the headers contain the API key
        assert "Authorization" in kwargs["headers"]
        assert f"Bearer {whisper_transcriber.api_key}" == kwargs["headers"]["Authorization"]

        # Check the files contain the correct model
        assert "model" in kwargs["files"]
        assert kwargs["files"]["model"][1] == whisper_transcriber.model


@pytest.mark.asyncio
async def test_transcribe_api_error(whisper_transcriber):
    """Test handling of API errors."""
    # Create a mock audio BytesIO object
    mock_audio = io.BytesIO(b"mock audio data")

    # Create a mock response with an error
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "Bad Request"

    # Create a mock client that returns our mock response
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value.post.return_value = mock_response

    # Patch the httpx.AsyncClient to return our mock
    with patch("httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(Exception) as excinfo:
            await whisper_transcriber.transcribe(mock_audio)

        # Verify the error message
        assert "Transcription failed: Bad Request" in str(excinfo.value)


@pytest.mark.asyncio
async def test_transcribe_timeout(whisper_transcriber):
    """Test handling of API timeout."""
    # Create a mock audio BytesIO object
    mock_audio = io.BytesIO(b"mock audio data")

    # Create a mock client that raises a timeout
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value.post.side_effect = httpx.TimeoutException("Timeout")

    # Patch the httpx.AsyncClient to return our mock
    with patch("httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(Exception) as excinfo:
            await whisper_transcriber.transcribe(mock_audio)

        # Verify the error message
        assert "Transcription API timed out" in str(excinfo.value)


def test_fuzzy_activation_matches():
    """Test fuzzy matching of activation phrases."""
    config = Config(
        openai_api_key="fake_key",
        activation_phrase="hey, speechless",
    )
    processor = TranscriptionProcessor(config)

    # Test various fuzzy matches for the activation phrase
    fuzzy_matches = [
        "okay speechless",
        "ok speechless",
        "ok, speechless",
        "okay speech less",
        "okay speech-less",
    ]

    for match in fuzzy_matches:
        assert processor.is_activation_phrase(match), f"Failed to match: {match}"
