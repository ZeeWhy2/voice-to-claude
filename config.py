"""Configuration management for VTC."""

import json
import os
from pathlib import Path
from typing import Optional, Any

CONFIG_FILE = Path(__file__).parent / "config.json"

DEFAULT_CONFIG = {
    "hotkey_record": None,       # Required, e.g. "ctrl+shift+r"
    "hotkey_copy": None,         # Required, e.g. "ctrl+shift+c"
    "input_device": None,        # None = system default
    "whisper_mode": "openai",    # "openai" or "local"
    "openai_api_key": None,      # Required if whisper_mode = "openai"
    "whisper_model": "base",     # For local: tiny/base/small/medium/large
    "language": "en"             # Transcription language hint
}

REQUIRED_FIELDS = ["hotkey_record", "hotkey_copy"]


class Config:
    """Manages application configuration."""

    def __init__(self):
        self._config: dict = {}
        self.load()

    def load(self) -> None:
        """Load configuration from file, creating defaults if needed."""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    self._config = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._config = {}

        # Merge with defaults for any missing keys
        for key, value in DEFAULT_CONFIG.items():
            if key not in self._config:
                self._config[key] = value

    def save(self) -> None:
        """Save current configuration to file."""
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self._config, f, indent=2)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self._config[key] = value

    def is_valid(self) -> bool:
        """Check if all required fields are set."""
        for field in REQUIRED_FIELDS:
            if not self._config.get(field):
                return False

        # If using OpenAI mode, API key is required
        if self._config.get("whisper_mode") == "openai":
            if not self._config.get("openai_api_key"):
                return False

        return True

    def get_missing_fields(self) -> list[str]:
        """Return list of missing required fields."""
        missing = []
        for field in REQUIRED_FIELDS:
            if not self._config.get(field):
                missing.append(field)

        if self._config.get("whisper_mode") == "openai":
            if not self._config.get("openai_api_key"):
                missing.append("openai_api_key")

        return missing

    @property
    def hotkey_record(self) -> Optional[str]:
        return self._config.get("hotkey_record")

    @hotkey_record.setter
    def hotkey_record(self, value: str) -> None:
        self._config["hotkey_record"] = value

    @property
    def hotkey_copy(self) -> Optional[str]:
        return self._config.get("hotkey_copy")

    @hotkey_copy.setter
    def hotkey_copy(self, value: str) -> None:
        self._config["hotkey_copy"] = value

    @property
    def input_device(self) -> Optional[int]:
        return self._config.get("input_device")

    @input_device.setter
    def input_device(self, value: Optional[int]) -> None:
        self._config["input_device"] = value

    @property
    def whisper_mode(self) -> str:
        return self._config.get("whisper_mode", "openai")

    @whisper_mode.setter
    def whisper_mode(self, value: str) -> None:
        self._config["whisper_mode"] = value

    @property
    def openai_api_key(self) -> Optional[str]:
        return self._config.get("openai_api_key")

    @openai_api_key.setter
    def openai_api_key(self, value: str) -> None:
        self._config["openai_api_key"] = value

    @property
    def whisper_model(self) -> str:
        return self._config.get("whisper_model", "base")

    @whisper_model.setter
    def whisper_model(self, value: str) -> None:
        self._config["whisper_model"] = value

    @property
    def language(self) -> str:
        return self._config.get("language", "en")

    @language.setter
    def language(self, value: str) -> None:
        self._config["language"] = value


# Global config instance
config = Config()
