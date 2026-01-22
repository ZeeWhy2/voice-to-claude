"""Global hotkey registration for VTC."""

import logging
import threading
from typing import Callable, Optional, Set

from pynput import keyboard

logger = logging.getLogger(__name__)


def parse_hotkey(hotkey_str: str) -> Set[str]:
    """Parse a hotkey string like 'ctrl+shift+r' into a set of key names."""
    if not hotkey_str:
        return set()

    parts = hotkey_str.lower().replace(" ", "").split("+")
    keys = set()

    for part in parts:
        # Normalize key names
        if part in ("ctrl", "control"):
            keys.add("ctrl")
        elif part in ("alt", "menu"):
            keys.add("alt")
        elif part in ("shift",):
            keys.add("shift")
        elif part in ("win", "super", "cmd", "command"):
            keys.add("cmd")
        else:
            keys.add(part)

    return keys


def key_to_str(key) -> Optional[str]:
    """Convert a pynput key to a string representation."""
    try:
        if hasattr(key, 'char') and key.char:
            return key.char.lower()
        elif hasattr(key, 'name'):
            name = key.name.lower()
            # Normalize modifier names
            if name in ("ctrl_l", "ctrl_r"):
                return "ctrl"
            elif name in ("alt_l", "alt_r", "alt_gr"):
                return "alt"
            elif name in ("shift_l", "shift_r"):
                return "shift"
            elif name in ("cmd_l", "cmd_r", "cmd"):
                return "cmd"
            return name
    except Exception:
        pass
    return None


class HotkeyManager:
    """Manages global hotkey registration and callbacks."""

    def __init__(self):
        self._hotkeys: dict[str, tuple[Set[str], Callable]] = {}
        self._pressed_keys: Set[str] = set()
        self._listener: Optional[keyboard.Listener] = None
        self._lock = threading.Lock()
        self._enabled = True

    def register(self, name: str, hotkey_str: str, callback: Callable) -> None:
        """Register a hotkey with a callback."""
        keys = parse_hotkey(hotkey_str)
        if not keys:
            logger.warning(f"Invalid hotkey string: {hotkey_str}")
            return

        with self._lock:
            self._hotkeys[name] = (keys, callback)
            logger.info(f"Registered hotkey '{name}': {hotkey_str}")

    def unregister(self, name: str) -> None:
        """Unregister a hotkey."""
        with self._lock:
            if name in self._hotkeys:
                del self._hotkeys[name]
                logger.info(f"Unregistered hotkey '{name}'")

    def update(self, name: str, hotkey_str: str) -> None:
        """Update an existing hotkey."""
        with self._lock:
            if name in self._hotkeys:
                _, callback = self._hotkeys[name]
                keys = parse_hotkey(hotkey_str)
                if keys:
                    self._hotkeys[name] = (keys, callback)
                    logger.info(f"Updated hotkey '{name}': {hotkey_str}")

    def start(self) -> None:
        """Start listening for hotkeys."""
        if self._listener is not None:
            return

        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self._listener.start()
        logger.info("Hotkey listener started")

    def stop(self) -> None:
        """Stop listening for hotkeys."""
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
            logger.info("Hotkey listener stopped")

    def enable(self) -> None:
        """Enable hotkey processing."""
        self._enabled = True

    def disable(self) -> None:
        """Disable hotkey processing (for settings capture)."""
        self._enabled = False

    def _on_press(self, key) -> None:
        """Handle key press event."""
        key_str = key_to_str(key)
        if key_str:
            self._pressed_keys.add(key_str)

            if self._enabled:
                self._check_hotkeys()

    def _on_release(self, key) -> None:
        """Handle key release event."""
        key_str = key_to_str(key)
        if key_str and key_str in self._pressed_keys:
            self._pressed_keys.discard(key_str)

    def _check_hotkeys(self) -> None:
        """Check if any registered hotkey is pressed."""
        with self._lock:
            for name, (keys, callback) in self._hotkeys.items():
                if keys and keys.issubset(self._pressed_keys):
                    # Clear pressed keys to prevent repeat triggers
                    self._pressed_keys.clear()
                    logger.debug(f"Hotkey triggered: {name}")
                    # Run callback in separate thread to not block listener
                    threading.Thread(target=callback, daemon=True).start()
                    break


class HotkeyCapture:
    """Captures a hotkey combination from user input."""

    def __init__(self, callback: Callable[[str], None]):
        self.callback = callback
        self._pressed: Set[str] = set()
        self._listener: Optional[keyboard.Listener] = None
        self._capturing = False

    def start(self) -> None:
        """Start capturing hotkey input."""
        self._pressed.clear()
        self._capturing = True
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self._listener.start()

    def stop(self) -> None:
        """Stop capturing hotkey input."""
        self._capturing = False
        if self._listener:
            self._listener.stop()
            self._listener = None

    def _on_press(self, key) -> None:
        """Handle key press during capture."""
        if not self._capturing:
            return

        key_str = key_to_str(key)
        if key_str:
            self._pressed.add(key_str)

    def _on_release(self, key) -> None:
        """Handle key release during capture."""
        if not self._capturing or not self._pressed:
            return

        # When any key is released, finalize the hotkey
        self._capturing = False

        # Build hotkey string with modifiers first
        modifiers = []
        regular = []
        for k in self._pressed:
            if k in ("ctrl", "alt", "shift", "cmd"):
                modifiers.append(k)
            else:
                regular.append(k)

        # Sort modifiers for consistent ordering
        modifiers.sort(key=lambda x: ["ctrl", "alt", "shift", "cmd"].index(x)
                       if x in ["ctrl", "alt", "shift", "cmd"] else 99)

        hotkey_str = "+".join(modifiers + regular)
        self._pressed.clear()

        if self._listener:
            self._listener.stop()
            self._listener = None

        self.callback(hotkey_str)
