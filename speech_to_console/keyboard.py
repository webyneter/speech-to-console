"""Keyboard interaction for typing in terminal."""

import os
import time

# Set environment variable to bypass tkinter check in PyAutoGUI
os.environ["PYAUTOGUI_RUNNING_HEADLESS"] = "True"

import pyautogui


class KeyboardController:
    """Controls keyboard input in the active terminal window."""

    def __init__(self, delay_between_chars: float = 0.01):
        """Initialize the keyboard controller.

        Args:
            delay_between_chars: Delay between keypresses in seconds
        """
        self.delay = delay_between_chars
        # Disable fail-safe since we're only typing text, not controlling mouse movements
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = self.delay

    def type_text(self, text: str) -> None:
        """Type text into the active window.

        Args:
            text: Text to type
        """
        # Give user time to switch to terminal if needed
        time.sleep(0.5)

        # Type the text with the configured delay between keystrokes
        pyautogui.write(text, interval=self.delay)

    def press_enter(self) -> None:
        """Press Enter key."""
        pyautogui.press("enter")

    def press_escape(self) -> None:
        """Press Escape key."""
        pyautogui.press("escape")

    def type_command(self, command: str, execute: bool = True) -> None:
        """Type a command and optionally execute it.

        Args:
            command: Command to type
            execute: Whether to press Enter after typing
        """
        self.type_text(command)
        if execute:
            self.press_enter()
