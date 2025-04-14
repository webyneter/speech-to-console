"""Tests for the audio module."""

import io
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
        silent_threshold=100,
        min_audio_duration_seconds=0.5,
    )


def test_initialization():
    """Test that AudioRecorder initializes correctly."""
    recorder = AudioRecorder(
        rate=16000,
        channels=1,
        silent_threshold=100,
        min_audio_duration_seconds=0.5,
    )

    assert recorder.rate == 16000
    assert recorder.channels == 1
    assert recorder.silent_threshold == 100
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
    mock_input_stream.assert_called_once_with(
        samplerate=audio_recorder.rate,
        channels=audio_recorder.channels,
        dtype=audio_recorder.dtype,
        blocksize=audio_recorder.blocksize,
    )

    # Check that stream was started
    mock_stream.start.assert_called_once()
    assert audio_recorder.is_recording is True
    assert audio_recorder.stream == mock_stream


@patch("sounddevice.InputStream")
def test_stop_recording(mock_input_stream, audio_recorder):
    """Test that stop_recording stops and closes the stream."""
    mock_stream = MagicMock()
    mock_input_stream.return_value = mock_stream

    # First start recording
    audio_recorder.start_recording()

    # Then stop it
    audio_recorder.stop_recording()

    # Check that stream was stopped and closed
    mock_stream.stop.assert_called_once()
    mock_stream.close.assert_called_once()
    assert audio_recorder.is_recording is False
    assert audio_recorder.stream is None


@patch("sounddevice.InputStream")
def test_record_chunk(mock_input_stream, audio_recorder):
    """Test that record_chunk returns audio data."""
    mock_stream = MagicMock()
    mock_input_stream.return_value = mock_stream

    # Mock the read method to return some fake data
    sample_size = (audio_recorder.blocksize, audio_recorder.channels)
    fake_data = np.ones(sample_size, dtype=np.int16)
    mock_stream.read.return_value = (fake_data, False)

    # Start recording
    audio_recorder.start_recording()

    # Record a chunk
    data = audio_recorder.record_chunk()

    # Check that read was called with blocksize
    mock_stream.read.assert_called_once_with(audio_recorder.blocksize)

    # Check that the returned data is what we expected
    np.testing.assert_array_equal(data, fake_data)


@patch("sounddevice.InputStream")
@patch("numpy.abs")
def test_record_until_silence_basic(mock_np_abs, mock_input_stream, audio_recorder):
    """Test the basic functionality of record_until_silence."""
    # Setup mocks
    mock_stream = MagicMock()
    mock_input_stream.return_value = mock_stream

    # Create sample arrays with shapes matching expected output
    sample_size = (audio_recorder.blocksize, audio_recorder.channels)

    # Create frames with large amplitude variance to be detected as speech
    frame1 = np.ones(sample_size, dtype=np.int16) * 150
    frame2 = np.ones(sample_size, dtype=np.int16) * 150
    frame3 = np.ones(sample_size, dtype=np.int16) * 10

    # Mock amplitude standard deviation to pass speech detection
    mock_std = MagicMock(return_value=30.0)  # High enough to be considered speech
    mock_np_abs.return_value.std = mock_std
    mock_np_abs.return_value.max = MagicMock(side_effect=[150, 150, 10])

    # Setup mock return values
    mock_stream.read.side_effect = [
        (frame1, False),
        (frame2, False),
        (frame3, False),
    ]

    # Override speech quality checks
    with patch.object(
        audio_recorder,
        "last_recording_metadata",
        {"speech_quality": {"is_likely_speech": True, "amplitude_std": 30.0}},
    ):
        # Record until silence with threshold of 1 silent frame
        result = audio_recorder.record_until_silence(silence_threshold=1)

    # Verify read was called for each frame
    assert mock_stream.read.call_count == 3

    # Verify we got a non-empty result
    assert len(result) > 0


@patch("sounddevice.InputStream")
def test_noise_detection(mock_input_stream, audio_recorder):
    """Test that constant noise is detected and filtered."""
    mock_stream = MagicMock()
    mock_input_stream.return_value = mock_stream

    # Sample size for test audio frames
    sample_size = (audio_recorder.blocksize, audio_recorder.channels)

    # Create frames with constant amplitude (above threshold but low variance)
    # This simulates constant background noise
    frame1 = np.ones(sample_size, dtype=np.int16) * 120
    frame2 = np.ones(sample_size, dtype=np.int16) * 120
    frame3 = np.ones(sample_size, dtype=np.int16) * 120

    mock_stream.read.side_effect = [
        (frame1, False),
        (frame2, False),
        (frame3, False),
        (np.zeros(sample_size, dtype=np.int16), False),  # Silent frame to end
    ]

    # Record until silence
    result = audio_recorder.record_until_silence(silence_threshold=1)

    # Since this is constant noise with low variance, we should get zeros back
    assert np.all(result == 0)

    # Check that speech quality metadata indicates this isn't speech
    assert (
        audio_recorder.last_recording_metadata["speech_quality"]["is_likely_speech"]
        is False
    )


@patch("sounddevice.InputStream")
@patch("numpy.abs")
def test_true_speech_detection(mock_np_abs, mock_input_stream, audio_recorder):
    """Test that true speech with high variance is correctly identified."""
    mock_stream = MagicMock()
    mock_input_stream.return_value = mock_stream

    # Sample size for test audio frames
    sample_size = (audio_recorder.blocksize, audio_recorder.channels)

    # Create frames that simulate speech
    frame1 = np.random.randint(120, 200, sample_size, dtype=np.int16)
    frame2 = np.random.randint(100, 180, sample_size, dtype=np.int16)
    frame3 = np.random.randint(110, 190, sample_size, dtype=np.int16)

    # Setup mocks for amplitude calculations
    mock_std = MagicMock(return_value=40.0)  # High variance
    mock_np_abs.return_value.std = mock_std
    mock_np_abs.return_value.max = MagicMock(side_effect=[180, 170, 180, 0])

    mock_stream.read.side_effect = [
        (frame1, False),
        (frame2, False),
        (frame3, False),
        (np.zeros(sample_size, dtype=np.int16), False),  # Silent frame to end
    ]

    # Record until silence
    with patch.object(audio_recorder, "min_audio_duration_seconds", 0.1):
        result = audio_recorder.record_until_silence(silence_threshold=1)

    # Verify we got a non-empty result
    assert len(result) > 0
    assert not np.all(result == 0)

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

    # Check that we got a BytesIO object
    assert isinstance(bytes_io, io.BytesIO)

    # Check that it has some data
    assert bytes_io.getbuffer().nbytes > 0
