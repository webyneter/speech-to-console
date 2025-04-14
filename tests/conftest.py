"""Pytest configuration file."""

import sys
from unittest.mock import MagicMock

import pytest

# Mock pyautogui and related modules before they're imported
sys.modules["pyautogui"] = MagicMock()
sys.modules["mouseinfo"] = MagicMock()
sys.modules["Xlib"] = MagicMock()
sys.modules["Xlib.display"] = MagicMock()


def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line("markers", "asyncio: mark test as an asyncio coroutine")


@pytest.fixture
def mock_keyboard_controller(monkeypatch):
    """Provide a mock keyboard controller."""
    # Create a mock KeyboardController
    mock_controller = MagicMock()
    mock_controller.type_text = MagicMock()
    mock_controller.type_command = MagicMock()
    mock_controller.press_enter = MagicMock()
    mock_controller.press_escape = MagicMock()
    mock_controller.delay = 0.01

    # Patch the import
    monkeypatch.setattr(
        "speech_to_console.keyboard.KeyboardController",
        lambda *args, **kwargs: mock_controller,
    )

    return mock_controller
