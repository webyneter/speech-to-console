"""Audio recording and processing functionality."""
import io
import wave
from typing import Generator, Optional

import numpy as np
import sounddevice as sd
import soundfile as sf


class AudioRecorder:
    """Handles audio recording from microphone."""

    def __init__(
        self,
        rate: int = 16000,
        channels: int = 1,
        dtype: str = "int16",
        blocksize: int = 1024,
    ):
        """Initialize the audio recorder.
        
        Args:
            rate: Sample rate
            channels: Number of audio channels (1=mono, 2=stereo)
            dtype: Data type for audio samples
            blocksize: Block size for audio processing
        """
        self.rate = rate
        self.channels = channels
        self.dtype = dtype
        self.blocksize = blocksize
        self.is_recording = False
        self.stream = None
        self.silent_threshold = 100  # Adjust as needed
        
        # Format mapping for wave module
        self.format_map = {
            "int16": 2,
            "int32": 4,
            "float32": 4,
        }
    
    def start_recording(self) -> None:
        """Start audio recording."""
        if self.is_recording:
            return
        
        self.stream = sd.InputStream(
            samplerate=self.rate,
            channels=self.channels,
            dtype=self.dtype,
            blocksize=self.blocksize,
        )
        self.stream.start()
        self.is_recording = True
    
    def stop_recording(self) -> None:
        """Stop audio recording."""
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        self.is_recording = False
    
    def __del__(self) -> None:
        """Clean up resources."""
        self.stop_recording()
    
    def record_chunk(self) -> np.ndarray:
        """Record a single chunk of audio.
        
        Returns:
            Audio chunk as numpy array
        """
        if not self.is_recording:
            self.start_recording()
        
        audio_data, overflowed = self.stream.read(self.blocksize)
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
        self.start_recording()
        frames = []
        max_chunks = int(self.rate / self.blocksize * max_seconds)
        silent_chunks = 0
        
        for _ in range(max_chunks):
            data = self.record_chunk()
            frames.append(data)
            
            # Check for silence
            if np.abs(data).max() < self.silent_threshold:
                silent_chunks += 1
                if silent_chunks >= silence_threshold:
                    break
            else:
                silent_chunks = 0
        
        return np.concatenate(frames)
    
    def record_continuously(self) -> Generator[np.ndarray, None, None]:
        """Record audio continuously in chunks.
        
        Yields:
            Audio chunks as numpy arrays
        """
        self.start_recording()
        
        try:
            while self.is_recording:
                yield self.record_chunk()
        finally:
            self.stop_recording()
    
    def audio_to_bytes_io(self, audio_data: np.ndarray) -> io.BytesIO:
        """Convert audio data to a BytesIO object in WAV format.
        
        Args:
            audio_data: Audio data as numpy array
        
        Returns:
            BytesIO object containing WAV data
        """
        bytes_io = io.BytesIO()
        
        with wave.open(bytes_io, "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.format_map.get(self.dtype, 2))
            wf.setframerate(self.rate)
            wf.writeframes(audio_data.tobytes())
        
        bytes_io.seek(0)
        return bytes_io
    
    def save_audio(self, audio_data: np.ndarray, filename: str) -> None:
        """Save audio data to a WAV file.
        
        Args:
            audio_data: Audio data as numpy array
            filename: Output filename
        """
        sf.write(filename, audio_data, self.rate, format="WAV")