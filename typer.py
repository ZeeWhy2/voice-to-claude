"""Simulated typing into active window for VTC."""

import logging
import time
from typing import Optional

from pynput.keyboard import Controller, Key

logger = logging.getLogger(__name__)

# Typing delay between characters (seconds)
DEFAULT_DELAY = 0.01


class Typer:
    """Simulates typing text into the active window."""

    def __init__(self, delay: float = DEFAULT_DELAY):
        self.delay = delay
        self._controller = Controller()

    def type_text(self, text: str, delay: Optional[float] = None) -> None:
        """
        Type text character by character into the active window.

        Args:
            text: The text to type
            delay: Optional override for delay between characters
        """
        if not text:
            return

        char_delay = delay if delay is not None else self.delay

        logger.info(f"Typing {len(text)} characters")

        for char in text:
            try:
                self._controller.type(char)
                if char_delay > 0:
                    time.sleep(char_delay)
            except Exception as e:
                logger.error(f"Failed to type character '{char}': {e}")
                # Try to continue with remaining characters

        logger.info("Typing complete")

    def type_fast(self, text: str) -> None:
        """Type text as fast as possible (no delay)."""
        self.type_text(text, delay=0)

    def press_key(self, key: Key) -> None:
        """Press a special key."""
        try:
            self._controller.press(key)
            self._controller.release(key)
        except Exception as e:
            logger.error(f"Failed to press key {key}: {e}")

    def press_enter(self) -> None:
        """Press the Enter key."""
        self.press_key(Key.enter)

    def press_tab(self) -> None:
        """Press the Tab key."""
        self.press_key(Key.tab)


def copy_to_clipboard(text: str) -> bool:
    """
    Copy text to the system clipboard.

    Uses tkinter for cross-platform clipboard access.
    """
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()  # Required for clipboard to persist
        root.destroy()
        logger.info("Text copied to clipboard")
        return True
    except Exception as e:
        logger.error(f"Failed to copy to clipboard: {e}")
        return False


def get_from_clipboard() -> Optional[str]:
    """
    Get text from the system clipboard.

    Uses tkinter for cross-platform clipboard access.
    """
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        text = root.clipboard_get()
        root.destroy()
        return text
    except Exception as e:
        logger.error(f"Failed to get from clipboard: {e}")
        return None
