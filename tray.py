"""System tray icon and menu for VTC."""

import logging
import threading
from typing import Callable, Optional

from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem as Item

logger = logging.getLogger(__name__)


def create_icon_image(color: str = "#4CAF50", recording: bool = False) -> Image.Image:
    """
    Create a simple icon image for the system tray.

    Args:
        color: Base color for the icon
        recording: If True, show recording indicator (red dot)
    """
    size = 64
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Draw microphone shape (simplified)
    mic_color = "#ff4444" if recording else color

    # Microphone body (rounded rectangle approximation)
    draw.ellipse([20, 8, 44, 40], fill=mic_color)
    draw.rectangle([20, 20, 44, 40], fill=mic_color)

    # Microphone stand
    draw.arc([16, 30, 48, 54], 0, 180, fill=mic_color, width=4)
    draw.line([32, 54, 32, 60], fill=mic_color, width=4)
    draw.line([22, 60, 42, 60], fill=mic_color, width=4)

    # Recording indicator (red dot)
    if recording:
        draw.ellipse([46, 4, 58, 16], fill="#ff0000")

    return image


class SystemTray:
    """Manages the system tray icon and menu."""

    def __init__(
        self,
        on_settings: Callable[[], None],
        on_quit: Callable[[], None]
    ):
        self._on_settings = on_settings
        self._on_quit = on_quit
        self._icon: Optional[pystray.Icon] = None
        self._recording = False
        self._thread: Optional[threading.Thread] = None

    def _create_menu(self) -> pystray.Menu:
        """Create the right-click menu."""
        return pystray.Menu(
            Item("Settings", self._settings_clicked),
            Item("Quit", self._quit_clicked)
        )

    def _settings_clicked(self, icon, item) -> None:
        """Handle Settings menu click."""
        logger.debug("Settings menu clicked")
        self._on_settings()

    def _quit_clicked(self, icon, item) -> None:
        """Handle Quit menu click."""
        logger.debug("Quit menu clicked")
        self.stop()
        self._on_quit()

    def start(self) -> None:
        """Start the system tray icon."""
        if self._icon is not None:
            return

        image = create_icon_image(recording=False)
        self._icon = pystray.Icon(
            "vtc",
            image,
            "Voice-to-Claude",
            menu=self._create_menu()
        )

        # Run in separate thread
        self._thread = threading.Thread(target=self._icon.run, daemon=True)
        self._thread.start()
        logger.info("System tray started")

    def stop(self) -> None:
        """Stop the system tray icon."""
        if self._icon:
            self._icon.stop()
            self._icon = None
        logger.info("System tray stopped")

    def set_recording(self, recording: bool) -> None:
        """Update icon to show recording state."""
        if not self._icon:
            return

        self._recording = recording
        image = create_icon_image(recording=recording)
        self._icon.icon = image

        if recording:
            self._icon.title = "Voice-to-Claude (Recording)"
        else:
            self._icon.title = "Voice-to-Claude"

    def notify(self, title: str, message: str) -> None:
        """Show a system notification."""
        if self._icon:
            try:
                self._icon.notify(message, title)
            except Exception as e:
                logger.error(f"Failed to show notification: {e}")
