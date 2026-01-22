"""Floating status overlay for VTC."""

import logging
import threading
import tkinter as tk
from typing import Optional

logger = logging.getLogger(__name__)


class StatusOverlay:
    """A floating overlay window showing recording/processing status."""

    def __init__(self):
        self._root: Optional[tk.Tk] = None
        self._label: Optional[tk.Label] = None
        self._visible = False
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None

    def _create_window(self) -> None:
        """Create the overlay window."""
        self._root = tk.Tk()
        self._root.title("VTC Status")

        # Remove window decorations
        self._root.overrideredirect(True)

        # Make window always on top
        self._root.attributes("-topmost", True)

        # Semi-transparent (Windows-specific, may need adjustment for other OS)
        try:
            self._root.attributes("-alpha", 0.85)
        except tk.TclError:
            pass

        # Create label with styling
        self._label = tk.Label(
            self._root,
            text="",
            font=("Segoe UI", 14, "bold"),
            fg="white",
            bg="#333333",
            padx=20,
            pady=10
        )
        self._label.pack()

        # Position window at top-center of screen
        self._root.update_idletasks()
        screen_width = self._root.winfo_screenwidth()
        window_width = self._root.winfo_width()
        x = (screen_width - window_width) // 2
        y = 50  # 50 pixels from top
        self._root.geometry(f"+{x}+{y}")

        # Hide initially
        self._root.withdraw()

    def _run_mainloop(self) -> None:
        """Run the tkinter mainloop in a separate thread."""
        self._create_window()
        self._root.mainloop()

    def start(self) -> None:
        """Start the overlay system."""
        if self._thread is not None:
            return

        self._thread = threading.Thread(target=self._run_mainloop, daemon=True)
        self._thread.start()

        # Give the window time to initialize
        import time
        time.sleep(0.1)

    def stop(self) -> None:
        """Stop the overlay system."""
        if self._root:
            try:
                self._root.quit()
            except Exception:
                pass
        self._thread = None

    def show(self, text: str, color: str = "#333333") -> None:
        """Show the overlay with specified text and background color."""
        if not self._root:
            return

        def _update():
            try:
                self._label.config(text=text, bg=color)
                self._root.update_idletasks()

                # Reposition to center
                screen_width = self._root.winfo_screenwidth()
                window_width = self._root.winfo_width()
                x = (screen_width - window_width) // 2
                y = 50
                self._root.geometry(f"+{x}+{y}")

                self._root.deiconify()
                self._root.lift()
                self._visible = True
            except Exception as e:
                logger.error(f"Failed to show overlay: {e}")

        try:
            self._root.after(0, _update)
        except Exception as e:
            logger.error(f"Failed to schedule overlay update: {e}")

    def hide(self) -> None:
        """Hide the overlay."""
        if not self._root:
            return

        def _hide():
            try:
                self._root.withdraw()
                self._visible = False
            except Exception as e:
                logger.error(f"Failed to hide overlay: {e}")

        try:
            self._root.after(0, _hide)
        except Exception as e:
            logger.error(f"Failed to schedule overlay hide: {e}")

    def show_recording(self) -> None:
        """Show 'Recording...' status."""
        self.show("🎤 Recording...", "#c0392b")  # Red background

    def show_processing(self) -> None:
        """Show 'Processing...' status."""
        self.show("⏳ Processing...", "#2980b9")  # Blue background

    def show_copied(self) -> None:
        """Show brief 'Copied!' notification."""
        self.show("📋 Copied!", "#27ae60")  # Green background

        # Auto-hide after 1 second
        if self._root:
            self._root.after(1000, self.hide)

    def show_error(self, message: str = "Error") -> None:
        """Show error status."""
        self.show(f"❌ {message}", "#e74c3c")  # Red background

        # Auto-hide after 2 seconds
        if self._root:
            self._root.after(2000, self.hide)

    @property
    def is_visible(self) -> bool:
        """Check if overlay is currently visible."""
        return self._visible
