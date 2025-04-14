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
