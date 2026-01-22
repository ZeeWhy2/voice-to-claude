"""Audio recording functionality for VTC."""

import logging
import tempfile
import threading
from pathlib import Path
from typing import Optional, Callable

import sounddevice as sd
import soundfile as sf
import numpy as np

logger = logging.getLogger(__name__)

SAMPLE_RATE = 16000  # Whisper expects 16kHz
CHANNELS = 1


class AudioRecorder:
    """Records audio from the selected input device."""

    def __init__(self, device: Optional[int] = None):
        self.device = device
        self._recording = False
        self._audio_data: list[np.ndarray] = []
        self._stream: Optional[sd.InputStream] = None
        self._lock = threading.Lock()

    def set_device(self, device: Optional[int]) -> None:
        """Set the input device to use."""
        self.device = device

    def start(self) -> None:
        """Start recording audio."""
        with self._lock:
            if self._recording:
                logger.warning("Already recording")
                return

            self._audio_data = []
            self._recording = True

            try:
                self._stream = sd.InputStream(
                    device=self.device,
                    samplerate=SAMPLE_RATE,
                    channels=CHANNELS,
                    dtype=np.float32,
                    callback=self._audio_callback
                )
                self._stream.start()
                logger.info("Recording started")
            except Exception as e:
                self._recording = False
                logger.error(f"Failed to start recording: {e}")
                raise

    def stop(self) -> Optional[Path]:
        """Stop recording and save to a temporary WAV file."""
        with self._lock:
            if not self._recording:
                logger.warning("Not currently recording")
                return None

            self._recording = False

            if self._stream:
                self._stream.stop()
                self._stream.close()
                self._stream = None

            if not self._audio_data:
                logger.warning("No audio data recorded")
                return None

            # Combine all audio chunks
            audio = np.concatenate(self._audio_data)
            self._audio_data = []

            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(
                suffix=".wav",
                delete=False
            )
            temp_path = Path(temp_file.name)
            temp_file.close()

            sf.write(temp_path, audio, SAMPLE_RATE)
            logger.info(f"Recording saved to {temp_path}")

            return temp_path

    def _audio_callback(
        self,
        indata: np.ndarray,
        frames: int,
        time_info: dict,
        status: sd.CallbackFlags
    ) -> None:
        """Callback for audio stream."""
        if status:
            logger.warning(f"Audio callback status: {status}")

        if self._recording:
            self._audio_data.append(indata.copy())

    @property
    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self._recording

    @staticmethod
    def get_input_devices() -> list[tuple[int, str]]:
        """Get list of available input devices."""
        devices = []
        try:
            device_list = sd.query_devices()
            for i, device in enumerate(device_list):
                if device['max_input_channels'] > 0:
                    devices.append((i, device['name']))
        except Exception as e:
            logger.error(f"Failed to query devices: {e}")
        return devices

    @staticmethod
    def get_default_input_device() -> Optional[int]:
        """Get the default input device index."""
        try:
            return sd.default.device[0]
        except Exception:
            return None
