"""Tests for the keyboard module."""

from unittest.mock import patch

import pytest
from speech_to_console.keyboard import KeyboardController


@pytest.fixture
def keyboard_controller():
    """Create a test keyboard controller."""
    return KeyboardController(delay_between_chars=0.01)


@patch("pyautogui.write")
def test_type_text(mock_write, keyboard_controller):
    """Test typing text functionality."""
    test_text = "hello world"

    keyboard_controller.type_text(test_text)

    # Check that the text was typed with the correct delay
    mock_write.assert_called_once_with(test_text, interval=keyboard_controller.delay)


@patch("pyautogui.press")
def test_press_enter(mock_press, keyboard_controller):
    """Test pressing Enter key."""
    keyboard_controller.press_enter()

    mock_press.assert_called_once_with("enter")


@patch("pyautogui.press")
def test_press_escape(mock_press, keyboard_controller):
    """Test pressing Escape key."""
    keyboard_controller.press_escape()

    mock_press.assert_called_once_with("escape")


@patch("pyautogui.write")
@patch("pyautogui.press")
def test_type_command_with_execute(mock_press, mock_write, keyboard_controller):
    """Test typing a command and executing it."""
    test_command = "ls -la"

    keyboard_controller.type_command(test_command, execute=True)

    # Check that the command was typed and Enter was pressed
    mock_write.assert_called_once_with(test_command, interval=keyboard_controller.delay)
    mock_press.assert_called_once_with("enter")


@patch("pyautogui.write")
@patch("pyautogui.press")
def test_type_command_without_execute(mock_press, mock_write, keyboard_controller):
    """Test typing a command without executing it."""
    test_command = "rm -rf /"

    keyboard_controller.type_command(test_command, execute=False)

    # Check that the command was typed but Enter was not pressed
    mock_write.assert_called_once_with(test_command, interval=keyboard_controller.delay)
    mock_press.assert_not_called()
