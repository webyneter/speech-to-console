# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.5] - 2025-04-14

### Fixed
- Fix changelog rendering in GitHub releases

### Changed
- Release v0.3.4


## [0.3.4] - 2025-04-14

### Changed
- Empty release to test GitHub Actions workflow

## [0.3.3] - 2025-04-14

### Fixed
- Fix GitHub release notes to only show current version changes


## [0.3.2] - 2025-04-14

### Changed
- Increase audio sensitivity thresholds


## [0.3.1] - 2025-04-14

### Changed
- Update release workflow to only run on successful builds


## [0.3.0] - 2025-04-14

### Added
- Add build and test badge to README
- Add pre-commit hooks for auto-formatting and linting
- Add uv.lock file update to release process
- Add automated release workflow with GitHub Actions

### Fixed
- Fix release script to handle pre-commit hook modifications
- Fix CI test issues by mocking GUI dependencies
- Fix CI build issues

### Changed
- Update release workflow to publish to PyPI
- Update setup-headless-display-action to v3 in CI configuration
- Update release script to also update __init__.py version
- Update author information in pyproject.toml
- Streamline release process with a single script
- Update README.md to clarify tool usage and requirements
- Update README.md to include 'uv' package requirement

### Dependencies
- Bump speech-to-console version to 0.2.2


## [0.3.0] - 2025-04-14

### Added
- Add build and test badge to README
- Add pre-commit hooks for auto-formatting and linting
- Add uv.lock file update to release process
- Add automated release workflow with GitHub Actions

### Fixed
- Fix CI test issues by mocking GUI dependencies
- Fix CI build issues

### Changed
- Update release workflow to publish to PyPI
- Update setup-headless-display-action to v3 in CI configuration
- Update release script to also update __init__.py version
- Update author information in pyproject.toml
- Streamline release process with a single script
- Update README.md to clarify tool usage and requirements
- Update README.md to include 'uv' package requirement

### Dependencies
- Bump speech-to-console version to 0.2.2


## [0.3.0] - 2025-04-14

### Added
- Add build and test badge to README
- Add pre-commit hooks for auto-formatting and linting
- Add uv.lock file update to release process
- Add automated release workflow with GitHub Actions

### Fixed
- Fix CI test issues by mocking GUI dependencies
- Fix CI build issues

### Changed
- Update release workflow to publish to PyPI
- Update setup-headless-display-action to v3 in CI configuration
- Update release script to also update __init__.py version
- Update author information in pyproject.toml
- Streamline release process with a single script
- Update README.md to clarify tool usage and requirements
- Update README.md to include 'uv' package requirement

### Dependencies
- Bump speech-to-console version to 0.2.2


## [0.2.3] - 2025-04-14

### Added
- Add build and test badge to README
- Add pre-commit hooks for auto-formatting and linting
- Add uv.lock file update to release process
- Add automated release workflow with GitHub Actions

### Fixed
- Fix CI test issues by mocking GUI dependencies
- Fix CI build issues

### Changed
- Update release workflow to publish to PyPI
- Update setup-headless-display-action to v3 in CI configuration
- Update release script to also update __init__.py version
- Update author information in pyproject.toml
- Streamline release process with a single script
- Update README.md to clarify tool usage and requirements
- Update README.md to include 'uv' package requirement

### Dependencies
- Bump speech-to-console version to 0.2.2


### Added
- Automated GitHub releases via GitHub Actions on tag pushes
- Automatic changelog updates on releases

## [0.2.0] - 2025-04-14

### Added
- Streaming transcription support for improved responsiveness
- Parallel processing of audio chunks for faster results
- Support for multiple activation and deactivation phrases
- New config options: `USE_STREAMING` and `STREAM_CHUNK_SIZE_MS`

### Fixed
- Fixed streaming audio transcription errors
- Improved deactivation phrase detection and handling
- Added fuzzy matching for deactivation phrases
- Fixed issue where deactivation phrases weren't properly stopping transcription

### Changed
- Reduced default streaming chunk size for improved responsiveness
- Made transcription process more resilient with better error handling
- Enhanced README with detailed streaming documentation
- Dynamically generate fuzzy matching based on activation phrases

## [0.1.0] - 2025-04-14

### Added
- Initial release of speech-to-console
- Core functionality for speech-to-text transcription using OpenAI's Whisper API
- Voice-activated command transcription for terminal
- Support for activation with custom phrase and deactivation with multiple phrases
- Advanced noise detection for better accuracy
- Comprehensive unit tests for AudioRecorder, KeyboardController, and WhisperTranscriber

### Fixed
- Enhanced noise detection with amplitude variance analysis
- Fixed issues with random gibberish transcriptions
- Fixed transcription handling of activation/deactivation phrases
- Fixed command extraction to properly handle different phrase variants

### Changed
- Updated README with detailed instructions and troubleshooting
- Improved logging with detailed diagnostics for speech characteristics
- Adjusted audio sensitivity settings for different environments
- Updated activation phrase to be more distinctive and reliable

[Unreleased]: https://github.com/webyneter/speech-to-console/compare/v0.3.5...HEAD
[0.3.5]: https://github.com/webyneter/speech-to-console/compare/v0.3.3...v0.3.5
[0.3.3]: https://github.com/webyneter/speech-to-console/compare/v0.3.2...v0.3.3
[0.3.2]: https://github.com/webyneter/speech-to-console/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/webyneter/speech-to-console/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/webyneter/speech-to-console/compare/v0.2.2...v0.3.0
[0.2.3]: https://github.com/webyneter/speech-to-console/compare/v0.2.2...v0.2.3
[0.2.2]: https://github.com/webyneter/speech-to-console/compare/v0.2.0...v0.2.2
[0.2.0]: https://github.com/webyneter/speech-to-console/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/webyneter/speech-to-console/releases/tag/v0.1.0
