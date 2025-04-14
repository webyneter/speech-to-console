# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build and Test Commands
- Install dependencies: `uv sync`
- Run all tests: `pytest`
- Linting and formatting: `ruff check .` and `ruff format .`
- Run CLI: `python -m speech_to_console [COMMAND]` or `speech-to-console [COMMAND]`

## Code Style Guidelines
- Python version: 3.12+
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
