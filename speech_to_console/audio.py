"""Audio recording and processing functionality."""

import io
import time
import wave
from typing import Generator

import numpy as np
import sounddevice as sd
import soundfile as sf
import structlog

# Get a logger for this module
logger = structlog.get_logger()


class AudioRecorder:
    """Handles audio recording from microphone."""

    def __init__(
        self,
        rate: int = 16000,
        channels: int = 1,
        dtype: str = "int16",
        blocksize: int = 1024,
        silent_threshold: int = 50,
        min_audio_duration_seconds: float = 0.5,
    ):
        """Initialize the audio recorder.

        Args:
            rate: Sample rate
            channels: Number of audio channels (1=mono, 2=stereo)
            dtype: Data type for audio samples
            blocksize: Block size for audio processing
            silent_threshold: Threshold for silence detection (lower = more sensitive)
            min_audio_duration_seconds: Minimum duration for valid speech detection
        """
        # Keep a dictionary of audio metadata for the last recorded audio
        self.last_recording_metadata = {"active_speech_duration": 0.0}
        self.rate = rate
        self.channels = channels
        self.dtype = dtype
        self.blocksize = blocksize
        self.is_recording = False
        self.stream = None
        self.silent_threshold = silent_threshold  # From config or default
        self.min_audio_duration_seconds = min_audio_duration_seconds

        # Format mapping for wave module
        self.format_map = {
            "int16": 2,
            "int32": 4,
            "float32": 4,
        }

        logger.debug(
            "AudioRecorder initialized",
            rate=rate,
            channels=channels,
            dtype=dtype,
            blocksize=blocksize,
            silent_threshold=self.silent_threshold,
        )

    def start_recording(self) -> None:
        """Start audio recording."""
        if self.is_recording:
            logger.debug("Recording is already in progress")
            return

        logger.debug("Starting audio recording stream")
        self.stream = sd.InputStream(
            samplerate=self.rate,
            channels=self.channels,
            dtype=self.dtype,
            blocksize=self.blocksize,
        )
        self.stream.start()
        self.is_recording = True
        logger.debug("Audio recording started successfully")

    def stop_recording(self) -> None:
        """Stop audio recording."""
        if not self.stream:
            logger.debug("No active recording stream to stop")
            return

        logger.debug("Stopping audio recording stream")
        self.stream.stop()
        self.stream.close()
        self.stream = None
        self.is_recording = False
        logger.debug("Audio recording stopped")

    def __del__(self) -> None:
        """Clean up resources."""
        logger.debug("Cleaning up AudioRecorder resources")
        self.stop_recording()

    def record_chunk(self) -> np.ndarray:
        """Record a single chunk of audio.

        Returns:
            Audio chunk as numpy array
        """
        if not self.is_recording:
            logger.debug("Starting recording for chunk")
            self.start_recording()

        audio_data, overflowed = self.stream.read(self.blocksize)

        if overflowed:
            logger.warning("Audio buffer overflow detected")

        return audio_data

    def record_until_silence(
        self, max_seconds: int = 10, silence_threshold: int = 3
    ) -> np.ndarray:
        """Record audio until silence is detected or max duration reached.

        Args:
            max_seconds: Maximum recording duration in seconds
            silence_threshold: Number of silent chunks to trigger stop

        Returns:
            Recorded audio as numpy array
        """
        logger.debug(
            "Recording until silence",
            max_seconds=max_seconds,
            silence_threshold=silence_threshold,
        )

        self.start_recording()
        frames = []
        max_chunks = int(self.rate / self.blocksize * max_seconds)
        silent_chunks = 0
        start_time = time.time()

        # Track overall max amplitude to detect if any real speech occurred
        overall_max_amplitude = 0
        active_speech_duration = 0.0  # Track duration of active speech
        amplitude_variance = []  # Track amplitude variance for speech detection

        for _ in range(max_chunks):
            data = self.record_chunk()
            frames.append(data)

            # Check for silence by analyzing amplitude
            max_amplitude = np.abs(data).max()
            amplitude_std = np.abs(data).std()  # Standard deviation of amplitudes
            amplitude_variance.append(amplitude_std)
            overall_max_amplitude = max(overall_max_amplitude, max_amplitude)

            # Human speech has high variance in amplitude
            # Background noise typically has low variance
            is_likely_speech = amplitude_std > (self.silent_threshold * 0.15)

            if max_amplitude < self.silent_threshold:
                silent_chunks += 1
                logger.debug(
                    "Silent chunk detected",
                    amplitude=float(max_amplitude),
                    silent_chunks_count=silent_chunks,
                    threshold=self.silent_threshold,
                )

                if silent_chunks >= silence_threshold:
                    logger.debug("Silence threshold reached, stopping recording")
                    break
            else:
                # Only count as speech if it has high amplitude variance
                if is_likely_speech:
                    chunk_duration = len(data) / self.rate  # Duration in seconds
                    active_speech_duration += chunk_duration
                    silent_chunks = 0
                    logger.debug(
                        "Active speech detected",
                        amplitude=float(max_amplitude),
                        amplitude_std=float(amplitude_std),
                        chunk_duration=f"{chunk_duration:.3f}s",
                        active_speech_duration=f"{active_speech_duration:.3f}s",
                    )
                else:
                    # Has volume but low variance - likely constant noise
                    logger.debug(
                        "Constant noise detected (not speech)",
                        amplitude=float(max_amplitude),
                        amplitude_std=float(amplitude_std),
                        threshold=self.silent_threshold,
                    )

        # Calculate true speech ratio - how much of the recording had real speech
        # This helps identify more robust speech vs. background noise
        total_recorded_time = len(frames) * (self.blocksize / self.rate)
        true_speech_ratio = (
            active_speech_duration / total_recorded_time
            if total_recorded_time > 0
            else 0
        )

        # Calculate average amplitude variance (standard deviation)
        avg_amplitude_std = (
            sum(amplitude_variance) / len(amplitude_variance)
            if amplitude_variance
            else 0
        )

        # If maximum amplitude was too close to threshold or variance is too low,
        # this was probably just background noise or random sounds
        if (
            overall_max_amplitude < self.silent_threshold * 1.7  # Not loud enough
            or avg_amplitude_std
            < (self.silent_threshold * 0.1)  # Not enough variance (constant noise)
            or (
                true_speech_ratio < 0.5
                and active_speech_duration < self.min_audio_duration_seconds * 2
            )  # Not consistent speech
        ):
            # Store detailed diagnostics about why we're filtering this
            logger.debug(
                "Filtering out likely background noise or random sounds",
                overall_max_amplitude=float(overall_max_amplitude),
                threshold=self.silent_threshold,
                ratio=f"{float(overall_max_amplitude) / self.silent_threshold:.2f}x",
                active_speech_duration=f"{active_speech_duration:.3f}s",
                total_recorded_time=f"{total_recorded_time:.3f}s",
                true_speech_ratio=f"{true_speech_ratio:.2f}",
                avg_std=float(avg_amplitude_std),
                reason=(
                    "low amplitude"
                    if overall_max_amplitude < self.silent_threshold * 1.7
                    else "low amplitude variance"
                    if avg_amplitude_std < (self.silent_threshold * 0.1)
                    else "insufficient speech content"
                ),
            )

            # Store the speech duration in our metadata dictionary
            self.last_recording_metadata["active_speech_duration"] = 0.0
            self.last_recording_metadata["speech_quality"] = {
                "active_speech_duration": active_speech_duration,
                "total_recorded_time": total_recorded_time,
                "true_speech_ratio": true_speech_ratio,
                "amplitude_std": avg_amplitude_std,
                "amplitude_std_ratio": avg_amplitude_std / self.silent_threshold
                if self.silent_threshold > 0
                else 0,
                "is_likely_speech": False,
            }

            # Return empty frames to avoid processing background noise
            if len(frames) > 0:
                # Return the same shape but with zeros
                result = np.zeros_like(np.concatenate(frames))
                return result
            else:
                # Return empty array if no frames
                result = np.zeros(1, dtype=np.int16)
                return result

        elapsed_time = time.time() - start_time
        result = np.concatenate(frames)

        # Store the speech duration and quality metrics in our metadata dictionary
        self.last_recording_metadata["active_speech_duration"] = active_speech_duration
        self.last_recording_metadata["amplitude_info"] = {
            "max_amplitude": float(overall_max_amplitude),
            "threshold": self.silent_threshold,
            "ratio": float(overall_max_amplitude) / self.silent_threshold
            if self.silent_threshold > 0
            else 0,
        }
        self.last_recording_metadata["speech_quality"] = {
            "active_speech_duration": active_speech_duration,
            "total_recorded_time": total_recorded_time,
            "true_speech_ratio": true_speech_ratio,
            "amplitude_std": avg_amplitude_std,
            "amplitude_std_ratio": avg_amplitude_std / self.silent_threshold
            if self.silent_threshold > 0
            else 0,
            "is_likely_speech": True,
        }

        logger.debug(
            "Recorded audio with speech duration",
            active_speech_duration=f"{active_speech_duration:.3f}s",
            total_duration=f"{elapsed_time:.3f}s",
            max_amplitude=float(overall_max_amplitude),
            amplitude_std=float(avg_amplitude_std),
            amplitude_ratio=(
                f"{float(overall_max_amplitude) / self.silent_threshold:.2f}x"
                if self.silent_threshold > 0
                else "N/A"
            ),
            std_ratio=(
                f"{float(avg_amplitude_std) / self.silent_threshold:.2f}x"
                if self.silent_threshold > 0
                else "N/A"
            ),
            meets_minimum_duration=active_speech_duration
            >= self.min_audio_duration_seconds,
        )

        logger.debug(
            "Recording completed",
            chunks_recorded=len(frames),
            total_samples=len(result),
            duration_seconds=f"{elapsed_time:.2f}s",
        )

        return result

    def record_continuously(self) -> Generator[np.ndarray, None, None]:
        """Record audio continuously in chunks.

        Yields:
            Audio chunks as numpy arrays
        """
        logger.debug("Starting continuous recording")
        self.start_recording()

        try:
            while self.is_recording:
                yield self.record_chunk()
        finally:
            logger.debug("Stopping continuous recording")
            self.stop_recording()

    def audio_to_bytes_io(self, audio_data: np.ndarray) -> io.BytesIO:
        """Convert audio data to a BytesIO object in WAV format.

        Args:
            audio_data: Audio data as numpy array

        Returns:
            BytesIO object containing WAV data
        """
        logger.debug("Converting audio data to BytesIO", samples=len(audio_data))
        start_time = time.time()
        bytes_io = io.BytesIO()

        with wave.open(bytes_io, "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.format_map.get(self.dtype, 2))
            wf.setframerate(self.rate)
            wf.writeframes(audio_data.tobytes())

        bytes_io.seek(0)
        elapsed_time = time.time() - start_time

        logger.debug(
            "Audio conversion complete",
            bytes_size=bytes_io.getbuffer().nbytes,
            duration_seconds=f"{elapsed_time:.4f}s",
        )

        return bytes_io

    def save_audio(self, audio_data: np.ndarray, filename: str) -> None:
        """Save audio data to a WAV file.

        Args:
            audio_data: Audio data as numpy array
            filename: Output filename
        """
        logger.debug("Saving audio to file", filename=filename, samples=len(audio_data))
        sf.write(filename, audio_data, self.rate, format="WAV")
        logger.debug("Audio saved successfully", filename=filename)
