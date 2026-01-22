"""Settings GUI for VTC."""

import logging
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional

from config import Config
from recorder import AudioRecorder
from hotkeys import HotkeyCapture

logger = logging.getLogger(__name__)


class SettingsWindow:
    """Settings dialog window."""

    def __init__(
        self,
        config: Config,
        on_save: Optional[Callable[[], None]] = None,
        on_close: Optional[Callable[[], None]] = None
    ):
        self.config = config
        self._on_save = on_save
        self._on_close = on_close
        self._root: Optional[tk.Toplevel] = None
        self._capturing_hotkey: Optional[str] = None
        self._hotkey_capture: Optional[HotkeyCapture] = None

        # UI variables
        self._record_hotkey_var: Optional[tk.StringVar] = None
        self._copy_hotkey_var: Optional[tk.StringVar] = None
        self._device_var: Optional[tk.StringVar] = None
        self._whisper_mode_var: Optional[tk.StringVar] = None
        self._api_key_var: Optional[tk.StringVar] = None
        self._model_var: Optional[tk.StringVar] = None
        self._language_var: Optional[tk.StringVar] = None

        # Device mapping
        self._devices: list[tuple[int, str]] = []

    def show(self, parent: Optional[tk.Tk] = None) -> None:
        """Show the settings window."""
        if self._root is not None:
            self._root.lift()
            self._root.focus_force()
            return

        # Create window
        if parent:
            self._root = tk.Toplevel(parent)
        else:
            self._root = tk.Tk()

        self._root.title("VTC Settings")
        self._root.geometry("450x500")
        self._root.resizable(False, False)

        # Handle window close
        self._root.protocol("WM_DELETE_WINDOW", self._on_window_close)

        self._create_widgets()
        self._load_values()

        # Center window
        self._root.update_idletasks()
        width = self._root.winfo_width()
        height = self._root.winfo_height()
        x = (self._root.winfo_screenwidth() - width) // 2
        y = (self._root.winfo_screenheight() - height) // 2
        self._root.geometry(f"+{x}+{y}")

        if not parent:
            self._root.mainloop()

    def _create_widgets(self) -> None:
        """Create the settings UI widgets."""
        main_frame = ttk.Frame(self._root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Hotkeys Section ---
        hotkey_frame = ttk.LabelFrame(main_frame, text="Hotkeys", padding=10)
        hotkey_frame.pack(fill=tk.X, pady=(0, 15))

        # Record hotkey
        ttk.Label(hotkey_frame, text="Record Toggle:").grid(
            row=0, column=0, sticky=tk.W, pady=5
        )
        self._record_hotkey_var = tk.StringVar()
        record_entry = ttk.Entry(
            hotkey_frame,
            textvariable=self._record_hotkey_var,
            width=20,
            state="readonly"
        )
        record_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(
            hotkey_frame,
            text="Set",
            command=lambda: self._capture_hotkey("record"),
            width=8
        ).grid(row=0, column=2, pady=5)

        # Copy hotkey
        ttk.Label(hotkey_frame, text="Copy Last:").grid(
            row=1, column=0, sticky=tk.W, pady=5
        )
        self._copy_hotkey_var = tk.StringVar()
        copy_entry = ttk.Entry(
            hotkey_frame,
            textvariable=self._copy_hotkey_var,
            width=20,
            state="readonly"
        )
        copy_entry.grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(
            hotkey_frame,
            text="Set",
            command=lambda: self._capture_hotkey("copy"),
            width=8
        ).grid(row=1, column=2, pady=5)

        # --- Audio Section ---
        audio_frame = ttk.LabelFrame(main_frame, text="Audio Input", padding=10)
        audio_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(audio_frame, text="Input Device:").pack(anchor=tk.W)
        self._device_var = tk.StringVar()
        self._device_combo = ttk.Combobox(
            audio_frame,
            textvariable=self._device_var,
            state="readonly",
            width=45
        )
        self._device_combo.pack(fill=tk.X, pady=5)
        self._populate_devices()

        # --- Whisper Section ---
        whisper_frame = ttk.LabelFrame(main_frame, text="Transcription", padding=10)
        whisper_frame.pack(fill=tk.X, pady=(0, 15))

        # Mode selection
        ttk.Label(whisper_frame, text="Whisper Mode:").grid(
            row=0, column=0, sticky=tk.W, pady=5
        )
        self._whisper_mode_var = tk.StringVar()
        mode_frame = ttk.Frame(whisper_frame)
        mode_frame.grid(row=0, column=1, sticky=tk.W, pady=5)
        ttk.Radiobutton(
            mode_frame,
            text="OpenAI API",
            variable=self._whisper_mode_var,
            value="openai",
            command=self._on_mode_change
        ).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(
            mode_frame,
            text="Local",
            variable=self._whisper_mode_var,
            value="local",
            command=self._on_mode_change
        ).pack(side=tk.LEFT)

        # API Key
        ttk.Label(whisper_frame, text="OpenAI API Key:").grid(
            row=1, column=0, sticky=tk.W, pady=5
        )
        self._api_key_var = tk.StringVar()
        self._api_key_entry = ttk.Entry(
            whisper_frame,
            textvariable=self._api_key_var,
            width=35,
            show="*"
        )
        self._api_key_entry.grid(row=1, column=1, sticky=tk.W, pady=5)

        # Model selection (for local)
        ttk.Label(whisper_frame, text="Local Model:").grid(
            row=2, column=0, sticky=tk.W, pady=5
        )
        self._model_var = tk.StringVar()
        self._model_combo = ttk.Combobox(
            whisper_frame,
            textvariable=self._model_var,
            values=["tiny", "base", "small", "medium", "large"],
            state="readonly",
            width=15
        )
        self._model_combo.grid(row=2, column=1, sticky=tk.W, pady=5)

        # Language
        ttk.Label(whisper_frame, text="Language:").grid(
            row=3, column=0, sticky=tk.W, pady=5
        )
        self._language_var = tk.StringVar()
        language_combo = ttk.Combobox(
            whisper_frame,
            textvariable=self._language_var,
            values=["en", "es", "fr", "de", "it", "pt", "nl", "ja", "ko", "zh"],
            width=10
        )
        language_combo.grid(row=3, column=1, sticky=tk.W, pady=5)

        # --- Buttons ---
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(
            button_frame,
            text="Save",
            command=self._save,
            width=12
        ).pack(side=tk.RIGHT, padx=(5, 0))

        ttk.Button(
            button_frame,
            text="Cancel",
            command=self._on_window_close,
            width=12
        ).pack(side=tk.RIGHT)

    def _populate_devices(self) -> None:
        """Populate the device dropdown."""
        self._devices = AudioRecorder.get_input_devices()
        device_names = ["System Default"] + [name for _, name in self._devices]
        self._device_combo["values"] = device_names

    def _load_values(self) -> None:
        """Load current config values into UI."""
        self._record_hotkey_var.set(self.config.hotkey_record or "Not set")
        self._copy_hotkey_var.set(self.config.hotkey_copy or "Not set")

        # Device
        device_id = self.config.input_device
        if device_id is None:
            self._device_var.set("System Default")
        else:
            for idx, name in self._devices:
                if idx == device_id:
                    self._device_var.set(name)
                    break

        # Whisper settings
        self._whisper_mode_var.set(self.config.whisper_mode)
        self._api_key_var.set(self.config.openai_api_key or "")
        self._model_var.set(self.config.whisper_model)
        self._language_var.set(self.config.language)

        self._on_mode_change()

    def _on_mode_change(self) -> None:
        """Handle whisper mode change."""
        mode = self._whisper_mode_var.get()
        if mode == "openai":
            self._api_key_entry.config(state="normal")
            self._model_combo.config(state="disabled")
        else:
            self._api_key_entry.config(state="disabled")
            self._model_combo.config(state="readonly")

    def _capture_hotkey(self, hotkey_type: str) -> None:
        """Start capturing a hotkey."""
        self._capturing_hotkey = hotkey_type

        if hotkey_type == "record":
            self._record_hotkey_var.set("Press keys...")
        else:
            self._copy_hotkey_var.set("Press keys...")

        def on_captured(hotkey_str: str):
            if self._capturing_hotkey == "record":
                self._record_hotkey_var.set(hotkey_str or "Not set")
            else:
                self._copy_hotkey_var.set(hotkey_str or "Not set")
            self._capturing_hotkey = None
            self._hotkey_capture = None

        self._hotkey_capture = HotkeyCapture(on_captured)
        self._hotkey_capture.start()

    def _save(self) -> None:
        """Save settings and close."""
        # Validate
        record_hotkey = self._record_hotkey_var.get()
        copy_hotkey = self._copy_hotkey_var.get()

        if record_hotkey in ("Not set", "Press keys..."):
            messagebox.showerror("Error", "Record hotkey is required")
            return

        if copy_hotkey in ("Not set", "Press keys..."):
            messagebox.showerror("Error", "Copy hotkey is required")
            return

        mode = self._whisper_mode_var.get()
        if mode == "openai" and not self._api_key_var.get().strip():
            messagebox.showerror("Error", "OpenAI API key is required for OpenAI mode")
            return

        # Save values
        self.config.hotkey_record = record_hotkey
        self.config.hotkey_copy = copy_hotkey

        # Device
        device_name = self._device_var.get()
        if device_name == "System Default":
            self.config.input_device = None
        else:
            for idx, name in self._devices:
                if name == device_name:
                    self.config.input_device = idx
                    break

        self.config.whisper_mode = mode
        self.config.openai_api_key = self._api_key_var.get().strip()
        self.config.whisper_model = self._model_var.get()
        self.config.language = self._language_var.get()

        self.config.save()
        logger.info("Settings saved")

        if self._on_save:
            self._on_save()

        self._close()

    def _on_window_close(self) -> None:
        """Handle window close."""
        if self._hotkey_capture:
            self._hotkey_capture.stop()

        if self._on_close:
            self._on_close()

        self._close()

    def _close(self) -> None:
        """Close the window."""
        if self._root:
            self._root.destroy()
            self._root = None


def show_settings(config: Config, on_save: Optional[Callable] = None) -> None:
    """Show the settings window."""
    window = SettingsWindow(config, on_save=on_save)
    window.show()
