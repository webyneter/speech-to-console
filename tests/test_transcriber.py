"""Tests for the transcriber module."""

from speech_to_console.config import Config
from speech_to_console.transcriber import TranscriptionProcessor


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
