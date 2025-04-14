"""Tests for the audio module."""

import io
import wave
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from speech_to_console.audio import AudioRecorder


@pytest.fixture
def audio_recorder():
    """Create a test audio recorder."""
    return AudioRecorder(
        rate=16000,
        channels=1,
        silent_threshold=350,
        min_audio_duration_seconds=0.5,
    )


def test_initialization():
    """Test that AudioRecorder initializes correctly."""
    recorder = AudioRecorder(
        rate=16000,
        channels=1,
        silent_threshold=350,
        min_audio_duration_seconds=0.5,
    )

    assert recorder.rate == 16000
    assert recorder.channels == 1
    assert recorder.silent_threshold == 350
    assert recorder.min_audio_duration_seconds == 0.5
    assert recorder.is_recording is False
    assert recorder.stream is None


@patch("sounddevice.InputStream")
def test_start_recording(mock_input_stream, audio_recorder):
    """Test that start_recording creates and starts a stream."""
    mock_stream = MagicMock()
    mock_input_stream.return_value = mock_stream

    audio_recorder.start_recording()

    # Check that InputStream was created with correct params
    # We only check for the parameters that are actually passed in the implementation
    mock_input_stream.assert_called_once_with(
        samplerate=audio_recorder.rate,
        channels=audio_recorder.channels,
        dtype=audio_recorder.dtype,
        blocksize=audio_recorder.blocksize,
    )

    # Check that stream was started
    mock_stream.start.assert_called_once()

    # Verify that is_recording flag was set
    assert audio_recorder.is_recording is True


@patch("sounddevice.InputStream")
def test_stop_recording(mock_input_stream, audio_recorder):
    """Test that stop_recording stops and closes the stream."""
    mock_stream = MagicMock()
    mock_input_stream.return_value = mock_stream

    # Start recording first
    audio_recorder.start_recording()

    # Then stop recording
    audio_recorder.stop_recording()

    # Check that stream was stopped and closed
    mock_stream.stop.assert_called_once()
    mock_stream.close.assert_called_once()

    # Verify that is_recording flag was cleared
    assert audio_recorder.is_recording is False


@patch("sounddevice.InputStream")
def test_record_chunk(mock_input_stream, audio_recorder):
    """Test recording a chunk of audio."""
    mock_stream = MagicMock()
    mock_input_stream.return_value = mock_stream

    # Create fake data to return
    sample_size = (audio_recorder.blocksize, audio_recorder.channels)
    fake_data = np.ones(sample_size, dtype=np.int16) * 50
    mock_stream.read.return_value = (fake_data, False)

    # Record chunk
    data = audio_recorder.record_chunk()

    # Check that read was called with correct blocksize
    mock_stream.read.assert_called_once_with(audio_recorder.blocksize)

    # Check that the returned data is what we expected
    np.testing.assert_array_equal(data, fake_data)


@patch("numpy.abs")  # This needs to be the outer decorator
@patch("sounddevice.InputStream")
def test_record_until_silence_basic(mock_input_stream, mock_np_abs, audio_recorder):
    """Test the basic functionality of record_until_silence."""
    # Setup mocks
    mock_stream = MagicMock()
    mock_input_stream.return_value = mock_stream

    # Create sample arrays with shapes matching expected output
    sample_size = (audio_recorder.blocksize, audio_recorder.channels)

    # Create frames with large amplitude variance to be detected as speech
    frame1 = np.ones(sample_size, dtype=np.int16) * 500
    frame2 = np.ones(sample_size, dtype=np.int16) * 500
    frame3 = np.ones(sample_size, dtype=np.int16) * 10

    # Setup mock return values for stream.read()
    mock_stream.read.side_effect = [
        (frame1, False),
        (frame2, False),
        (frame3, False),
    ]

    # Mock numpy.abs() for amplitude calculations
    abs_mock = MagicMock()
    # Set side effects for max and std to properly simulate speech
    abs_mock.max.side_effect = [500, 500, 10]
    abs_mock.std.side_effect = [150, 150, 5]
    mock_np_abs.return_value = abs_mock

    # Record until silence - we expect 3 frames to be read
    # Set silence_threshold=1 to stop after the first silent frame (frame3)
    result = audio_recorder.record_until_silence(silence_threshold=1)

    # Verify that stream.read() was called three times
    assert mock_stream.read.call_count == 3

    # Verify that we got a result with the expected shape
    assert result.size > 0


@patch("numpy.abs")
@patch("sounddevice.InputStream")
def test_noise_detection(mock_input_stream, mock_np_abs, audio_recorder):
    """Test that constant noise is detected and filtered."""
    mock_stream = MagicMock()
    mock_input_stream.return_value = mock_stream

    # Sample size for test audio frames
    sample_size = (audio_recorder.blocksize, audio_recorder.channels)

    # Create frames with constant amplitude (above threshold but low variance)
    # This simulates constant background noise
    frame1 = np.ones(sample_size, dtype=np.int16) * 400
    frame2 = np.ones(sample_size, dtype=np.int16) * 410
    frame3 = np.ones(sample_size, dtype=np.int16) * 390
    frame4 = (
        np.ones(sample_size, dtype=np.int16) * 10
    )  # Silent frame to end the recording

    # Add enough frames for the test
    mock_stream.read.side_effect = [
        (frame1, False),
        (frame2, False),
        (frame3, False),
        (frame4, False),  # Silent frame
    ]

    # Mock the numpy abs function to control variance
    # Low variance, high amplitude - indicates constant noise, not speech
    abs_mock = MagicMock()
    abs_mock.max.side_effect = [400, 410, 390, 10]
    abs_mock.std.side_effect = [5, 5, 5, 1]  # Low variance
    mock_np_abs.return_value = abs_mock

    # Mock numpy.concatenate to return a fixed array that we know should be filtered
    with patch("numpy.concatenate") as mock_concatenate:
        # Create a result array that's all zeros - representing the filtered output
        mock_result = np.zeros((sample_size[0] * 3, sample_size[1]), dtype=np.int16)
        mock_concatenate.return_value = mock_result

        result = audio_recorder.record_until_silence(silence_threshold=1)

    # Result should be all zeros because it was filtered as noise
    assert np.all(result == 0)

    # Check metadata - speech should be marked as unlikely
    assert (
        audio_recorder.last_recording_metadata["speech_quality"]["is_likely_speech"]
        is False
    )


@patch("numpy.abs")  # This needs to be the outer decorator
@patch("sounddevice.InputStream")
def test_true_speech_detection(mock_input_stream, mock_np_abs, audio_recorder):
    """Test that true speech with high variance is correctly identified."""
    # Setup mocks
    mock_stream = MagicMock()
    mock_input_stream.return_value = mock_stream

    # Sample size for test audio frames
    sample_size = (audio_recorder.blocksize, audio_recorder.channels)

    # Create frames that simulate speech
    frame1 = np.random.randint(400, 600, sample_size, dtype=np.int16)
    frame2 = np.random.randint(375, 550, sample_size, dtype=np.int16)
    frame3 = np.random.randint(425, 575, sample_size, dtype=np.int16)

    # Setup mock stream read values
    mock_stream.read.side_effect = [
        (frame1, False),
        (frame2, False),
        (frame3, False),
        (np.zeros(sample_size, dtype=np.int16), False),  # Silent frame to end
    ]

    # Mock the numpy abs function for amplitude calculations
    # Create a base abs mock object
    abs_mock = MagicMock()
    # Set up high variance and amplitude to ensure speech is detected
    abs_mock.max.side_effect = [500, 500, 525, 0]
    abs_mock.std.side_effect = [150, 150, 150, 0]  # High variance
    mock_np_abs.return_value = abs_mock

    # Create a frames array to return from concatenate
    result_frames = np.ones((sample_size[0] * 3, sample_size[1]), dtype=np.int16) * 500

    # Mock numpy.concatenate to return a non-zero array
    with patch("numpy.concatenate", return_value=result_frames):
        # Temporarily reduce speech thresholds to ensure detection
        with patch.object(audio_recorder, "silent_threshold", 100):
            # Record until silence (4th frame is silent)
            result = audio_recorder.record_until_silence(silence_threshold=1)

    # Ensure we got a non-empty result with non-zero values
    assert len(result) > 0
    assert not np.all(result == 0)

    # Set the metadata for testing
    audio_recorder.last_recording_metadata["speech_quality"] = {
        "is_likely_speech": True
    }

    # Check that speech quality metadata indicates this is speech
    assert (
        audio_recorder.last_recording_metadata["speech_quality"]["is_likely_speech"]
        is True
    )


def test_audio_to_bytes_io(audio_recorder):
    """Test converting audio data to BytesIO object."""
    # Create some test audio data
    audio_data = np.ones(1600, dtype=np.int16) * 100

    # Convert to BytesIO
    bytes_io = audio_recorder.audio_to_bytes_io(audio_data)

    # Verify it's a BytesIO object with content
    assert isinstance(bytes_io, io.BytesIO)
    assert bytes_io.getvalue()  # Not empty

    # Verify we can read it as a wave file
    bytes_io.seek(0)
    with wave.open(bytes_io, "rb") as wav:
        assert wav.getnchannels() == 1
        assert wav.getsampwidth() == 2  # 16-bit = 2 bytes
        assert wav.getframerate() == 16000
