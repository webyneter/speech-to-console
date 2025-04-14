# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build and Test Commands
- Install dependencies: `uv sync`
- Run all tests: `uv run pytest`
- Linting and formatting: `uv run ruff check --fix .`
- Overall, any commands targeting the Python codebase must be run via `uv` 
- Launch CLI locally: `uv run speech-to-console`
- Launch CLI locally with the specified log level: `uv run speech-to-console --log-level DEBUG`

## Code Style Guidelines
- Python version: 3.10
- Package manager: uv with lock file
- CLI framework: Typer
- Follow PEP 8 and use ruff for code formatting/linting
- Use type hints for all function parameters and return values
- Line length: 88 characters (Ruff default)
- Error handling: Use explicit exception handling with specific exception types
- Naming: snake_case for variables/functions, PascalCase for classes
- Documentation: Docstrings for all public modules, classes, methods (Google style)

## Project Organization
This project is a speech-to-console utility that converts spoken commands to console/terminal operations.

## Claude Code Conversation History

```
  <analysis>
  I'll analyze the conversation chronologically to capture all key details:

  1. First phase: Fixing random gibberish transcriptions (continued from previous session)
     - User reported: Getting gibberish transcriptions from Whisper API even when not speaking
     - Context from previous session summary: Fixed activation detection, changed phrase to "okay, speechless", added noise filtering
     - The conversation continued with remaining issue of getting random transcriptions like "you", "Thanks for watching!", etc.
     - We implemented several fixes to address this noise issue

  2. Detailed implementation of speech duration filter:
     - Added MIN_AUDIO_DURATION_SECONDS (0.5s default) to filter short sounds
     - Added tracking of speech duration with audio_recorder.last_recording_metadata
     - Initially tried using attributes on NumPy arrays but switched to a dictionary approach
     - Used debug logging to track speech characteristics
     - Added various filters for detecting true speech vs noise

  3. Bug fixes when implementing solution:
     - Fixed an issue where adding attributes to NumPy arrays wasn't possible
     - Created a metadata dictionary to store speech quality metrics
     - Fixed formatting, docstring positions, and linting errors

  4. Further improvements for noise filtering:
     - Added amplitude variance analysis to distinguish speech from background noise
     - Updated SILENT_THRESHOLD from 50 to 400 for better noise filtering
     - Added detailed debug logging for speech characteristics
     - Considered but rejected filtering specific words as they might be valid commands

  5. Key files modified:
     - speech_to_console/audio.py: Enhanced audio detection with amplitude variance
     - speech_to_console/cli.py: Updated to skip low-quality audio and use metadata
     - speech_to_console/config.py: Added configuration for minimum speech duration
     - example.env: Added new configuration options
     - README.md: Updated with troubleshooting information

  6. Technical approach:
     - Used standard deviation of amplitude to detect speech vs. noise
     - Added true_speech_ratio to identify consistent speech
     - Increased default SILENT_THRESHOLD to better match typical environments
     - Added detailed diagnostic logging to help troubleshoot issues

  7. Most recent work:
     - Added amplitude variance analysis to distinguish speech from constant noise
     - Increased default SILENT_THRESHOLD to 400
     - Added enhanced debug logging
     - Fixed formatting and linting issues
     - Made a commit with these changes
  </analysis>

  <summary>
  1. Primary Request and Intent:
     The user experienced constant false transcriptions when using speech-to-console, with Whisper API producing gibberish even when no one was speaking. Their specific requests were:
     - Fix the system to disregard sounds happening outside of activation/deactivation phrases
     - Understand why gibberish is produced when not speaking
     - Address constant false positive transcriptions (like "you", "Thanks for watching!")
     - Find a solution that doesn't filter out specific words (which could be legitimate commands)

  2. Key Technical Concepts:
     - Speech recognition using OpenAI's Whisper API
     - Audio processing with numpy for silence and speech detection
     - Amplitude analysis for detecting true speech vs. background noise
     - Standard deviation (variance) analysis to distinguish speech from constant noise
     - Structured logging with detailed audio characteristics
     - Environment-specific audio threshold configuration
     - Voice activation/deactivation lifecycle management
     - PyAutoGUI for keyboard automation
     - Command-line interface using Typer
     - Asynchronous programming with asyncio

  3. Files and Code Sections:
     - `speech_to_console/audio.py`
        - Core audio recording and analysis functionality
        - Added amplitude variance (standard deviation) detection to distinguish speech from noise
        - Added speech quality metrics to track characteristics of recorded audio
        ```python
        # Human speech has high variance in amplitude
        # Background noise typically has low variance
        is_likely_speech = amplitude_std > (self.silent_threshold * 0.15)
        
        # Count as speech only if it has high amplitude variance
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
        ```
        - Added more comprehensive noise detection algorithm:
        ```python
        # Calculate average amplitude variance (standard deviation)
        avg_amplitude_std = sum(amplitude_variance) / len(amplitude_variance) if amplitude_variance else 0
        
        # If maximum amplitude was too close to threshold or variance is too low,
        # this was probably just background noise or random sounds
        if (
            overall_max_amplitude < self.silent_threshold * 1.7  # Not loud enough
            or avg_amplitude_std < (self.silent_threshold * 0.1)  # Not enough variance (constant noise)
            or (true_speech_ratio < 0.5 and active_speech_duration < self.min_audio_duration_seconds * 2)  # Not consistent speech
        ):
        ```
        - Used a metadata dictionary instead of NumPy attributes to track speech quality:
        ```python
        self.last_recording_metadata["speech_quality"] = {
            "active_speech_duration": active_speech_duration,
            "total_recorded_time": total_recorded_time,
            "true_speech_ratio": true_speech_ratio,
            "amplitude_std": avg_amplitude_std,
            "amplitude_std_ratio": avg_amplitude_std / self.silent_threshold if self.silent_threshold > 0 else 0,
            "is_likely_speech": True,
        }
        ```

     - `speech_to_console/cli.py`
        - Command-line interface and main processing loop
        - Updated to use speech quality metrics from metadata
        - Added detailed logging of speech characteristics:
        ```python
        logger.debug(
            "Transcription received",
            raw_text=transcription,
            is_active=is_active,
            in_valid_cycle=in_valid_cycle,
            speech_duration=f"{speech_duration:.3f}s",
            max_amplitude=amplitude_info.get("max_amplitude", 0),
            amplitude_ratio=amplitude_info.get("ratio", 0),
            amplitude_std=speech_quality.get("amplitude_std", 0),
            amplitude_std_ratio=speech_quality.get("amplitude_std_ratio", 0),
            text_length=len(transcription),
            word_count=len(transcription.split()),
            true_speech_ratio=speech_quality.get("true_speech_ratio", 0),
            is_likely_speech=speech_quality.get("is_likely_speech", False),
        )
        ```

     - `speech_to_console/config.py`
        - Added configuration for minimum speech duration
        ```python
        # Transcription filtering
        min_audio_duration_seconds: float = Field(
            0.5, description="Minimum audio duration in seconds to consider valid speech"
        )
        ```

     - `example.env`
        - Updated to include new configuration options
        ```
        # Audio sensitivity (lower = more sensitive, higher = less sensitive)
        # Adjust based on your environment:
        # - For quiet environments: 100-150
        # - For normal ambient noise: 200-300
        # - For noisy environments: 400-500
        SILENT_THRESHOLD=400
        
        # Minimum audio duration in seconds to be considered valid speech
        # Increase this value to filter out false transcriptions from background noise
        # Try values like 0.8 or 1.0 if you're getting random gibberish transcriptions
        MIN_AUDIO_DURATION_SECONDS=0.5
        ```

     - `README.md`
        - Updated with detailed troubleshooting information for different environments
        - Added information about the new noise detection techniques
        ```markdown
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
        ```

  4. Problem Solving:
     - Initial issue: System was treating background noise as speech
       - Debug logs showed consistent "Active speech detected" with amplitude 350-450
       - The default SILENT_THRESHOLD was too low (50-100)
       - The system couldn't distinguish constant noise from actual speech
     
     - Solutions implemented:
       - Added standard deviation (variance) analysis of amplitude to detect human speech vs. constant noise
       - Increased default SILENT_THRESHOLD to 400 to better match typical environments
       - Added speech quality metrics including amplitude-to-threshold ratios
       - Enhanced logging to show detailed diagnostics about speech characteristics
       - Fixed an issue with NumPy arrays not supporting attribute assignment by using a metadata dictionary
       - Improved the README with environment-specific troubleshooting advice

     - Solution approach rationale:
       - Human speech has high variance in amplitude (standard deviation)
       - Background noise often has consistent amplitude with low variance
       - By analyzing both the amplitude and its variance, we can better identify real speech
       - This approach doesn't filter specific words that might be legitimate commands

  5. Pending Tasks:
     No specific pending tasks were identified after implementing the noise detection improvements.

  6. Current Work:
     Immediately before this summary request, we had completed implementing and committing the amplitude variance analysis feature to better distinguish speech from background noise. The key changes were:

     - Added amplitude standard deviation analysis to detect speech vs. constant noise
     - Increased the default SILENT_THRESHOLD from 50-100 to 400
     - Added enhanced debug logging with detailed speech characteristics
     - Updated the README with environment-specific troubleshooting advice
     - Fixed formatting and linting issues

     These changes were committed with the message:
     ```
     Improve noise detection with amplitude variance analysis

     - Add amplitude variance (standard deviation) analysis to better detect speech vs. noise
     - Increase default silent_threshold to 400 for better noise filtering
     - Add enhanced diagnostics in debug logs to better understand noise patterns
     - Update README with more detailed troubleshooting advice for different environments
     - Fix formatting and linting issues
     ```

  7. Optional Next Step:
     There is no explicit next step as we had completed the task of improving noise detection with amplitude variance analysis and had committed all changes. The user would need to test these changes and provide feedback on whether the improved noise detection effectively addresses the gibberish 
  transcription issues. If additional refinements are needed, they would be based on that feedback.
  </summary>.
```
