"""Main entry point for Voice-to-Claude (VTC)."""

import logging
import sys
import threading
import time
from pathlib import Path
from typing import Optional

from config import config
from recorder import AudioRecorder
from transcriber import Transcriber, TranscriptionError
from hotkeys import HotkeyManager
from typer import Typer, copy_to_clipboard
from overlay import StatusOverlay
from tray import SystemTray
from settings_gui import SettingsWindow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path(__file__).parent / "vtc.log")
    ]
)
logger = logging.getLogger(__name__)


class VTCApp:
    """Main application class orchestrating all components."""

    def __init__(self):
        self._recorder: Optional[AudioRecorder] = None
        self._transcriber: Optional[Transcriber] = None
        self._hotkeys: Optional[HotkeyManager] = None
        self._typer: Optional[Typer] = None
        self._overlay: Optional[StatusOverlay] = None
        self._tray: Optional[SystemTray] = None

        self._last_transcription: Optional[str] = None
        self._recording = False
        self._processing = False
        self._running = False
        self._settings_window: Optional[SettingsWindow] = None

    def _init_components(self) -> None:
        """Initialize all components."""
        logger.info("Initializing components...")

        # Audio recorder
        self._recorder = AudioRecorder(device=config.input_device)

        # Transcriber
        self._transcriber = Transcriber(
            mode=config.whisper_mode,
            api_key=config.openai_api_key,
            model_size=config.whisper_model
        )

        # Typer
        self._typer = Typer()

        # Overlay
        self._overlay = StatusOverlay()
        self._overlay.start()

        # Hotkeys
        self._hotkeys = HotkeyManager()
        self._hotkeys.register("record", config.hotkey_record, self._on_record_hotkey)
        self._hotkeys.register("copy", config.hotkey_copy, self._on_copy_hotkey)

        # System tray
        self._tray = SystemTray(
            on_settings=self._open_settings,
            on_quit=self._quit
        )

        logger.info("Components initialized")

    def _on_record_hotkey(self) -> None:
        """Handle record hotkey press."""
        if self._processing:
            logger.debug("Ignoring hotkey - currently processing")
            return

        if self._recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self) -> None:
        """Start audio recording."""
        if self._recording:
            return

        logger.info("Starting recording")
        self._recording = True

        try:
            self._recorder.start()
            self._overlay.show_recording()
            self._tray.set_recording(True)
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            self._recording = False
            self._overlay.show_error("Mic error")

    def _stop_recording(self) -> None:
        """Stop recording and process audio."""
        if not self._recording:
            return

        logger.info("Stopping recording")
        self._recording = False
        self._processing = True

        self._overlay.show_processing()
        self._tray.set_recording(False)

        # Stop recording and get audio file
        audio_path = self._recorder.stop()

        if not audio_path:
            logger.warning("No audio recorded")
            self._processing = False
            self._overlay.hide()
            return

        # Process in background thread
        threading.Thread(
            target=self._process_audio,
            args=(audio_path,),
            daemon=True
        ).start()

    def _process_audio(self, audio_path: Path) -> None:
        """Process recorded audio (runs in background thread)."""
        try:
            logger.info("Transcribing audio...")
            text = self._transcriber.transcribe(audio_path, config.language)

            if text:
                logger.info(f"Transcription: {text[:50]}...")
                self._last_transcription = text

                # Hide overlay before typing
                self._overlay.hide()

                # Small delay to ensure overlay is hidden
                time.sleep(0.1)

                # Type the transcribed text
                self._typer.type_text(text)
            else:
                logger.warning("Empty transcription")
                self._overlay.show_error("No speech detected")

        except TranscriptionError as e:
            logger.error(f"Transcription error: {e}")
            self._overlay.show_error("Transcription failed")

        except Exception as e:
            logger.error(f"Processing error: {e}")
            self._overlay.show_error("Error")

        finally:
            self._processing = False

    def _on_copy_hotkey(self) -> None:
        """Handle copy last transcription hotkey."""
        if self._last_transcription:
            if copy_to_clipboard(self._last_transcription):
                self._overlay.show_copied()
            else:
                self._overlay.show_error("Copy failed")
        else:
            logger.debug("No transcription to copy")

    def _open_settings(self) -> None:
        """Open the settings window."""
        if self._settings_window is not None:
            return

        # Disable hotkeys while settings is open
        if self._hotkeys:
            self._hotkeys.disable()

        def on_save():
            self._apply_settings()

        def on_close():
            self._settings_window = None
            if self._hotkeys:
                self._hotkeys.enable()

        self._settings_window = SettingsWindow(
            config,
            on_save=on_save,
            on_close=on_close
        )

        # Run in a separate thread to not block
        threading.Thread(
            target=self._settings_window.show,
            daemon=True
        ).start()

    def _apply_settings(self) -> None:
        """Apply changed settings."""
        logger.info("Applying settings changes")

        # Update recorder device
        if self._recorder:
            self._recorder.set_device(config.input_device)

        # Update transcriber
        try:
            if self._transcriber:
                self._transcriber.set_mode(
                    config.whisper_mode,
                    config.openai_api_key,
                    config.whisper_model
                )
        except Exception as e:
            logger.error(f"Failed to update transcriber: {e}")

        # Update hotkeys
        if self._hotkeys:
            self._hotkeys.update("record", config.hotkey_record)
            self._hotkeys.update("copy", config.hotkey_copy)

    def _quit(self) -> None:
        """Quit the application."""
        logger.info("Quitting VTC")
        self._running = False

        # Stop components
        if self._hotkeys:
            self._hotkeys.stop()
        if self._overlay:
            self._overlay.stop()
        if self._tray:
            self._tray.stop()

        sys.exit(0)

    def run(self) -> None:
        """Run the application."""
        logger.info("Starting VTC")

        # Check if first run or missing config
        if not config.is_valid():
            missing = config.get_missing_fields()
            logger.info(f"Missing required config fields: {missing}")
            logger.info("Opening settings for first-time setup")

            # Show settings window for initial config
            def on_first_save():
                if config.is_valid():
                    self._start_app()
                else:
                    logger.error("Configuration still invalid after settings")
                    sys.exit(1)

            def on_first_close():
                if not config.is_valid():
                    logger.info("Settings closed without valid config - exiting")
                    sys.exit(0)

            window = SettingsWindow(config, on_save=on_first_save, on_close=on_first_close)
            window.show()
        else:
            self._start_app()

    def _start_app(self) -> None:
        """Start the main application after config is valid."""
        self._init_components()

        # Start listening for hotkeys
        self._hotkeys.start()

        # Start system tray
        self._tray.start()

        self._running = True
        logger.info("VTC is running")
        logger.info(f"Record hotkey: {config.hotkey_record}")
        logger.info(f"Copy hotkey: {config.hotkey_copy}")

        # Keep main thread alive
        try:
            while self._running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            logger.info("Interrupted")
            self._quit()


def main():
    """Main entry point."""
    app = VTCApp()
    app.run()


if __name__ == "__main__":
    main()
