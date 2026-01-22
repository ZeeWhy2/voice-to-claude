"""Whisper transcription backends for VTC."""

import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class TranscriberBackend(ABC):
    """Abstract base class for transcription backends."""

    @abstractmethod
    def transcribe(self, audio_path: Path, language: str = "en") -> str:
        """Transcribe audio file to text."""
        pass


class OpenAIWhisperBackend(TranscriberBackend):
    """OpenAI Whisper API backend."""

    def __init__(self, api_key: str):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)

    def transcribe(self, audio_path: Path, language: str = "en") -> str:
        """Transcribe using OpenAI Whisper API."""
        try:
            with open(audio_path, "rb") as audio_file:
                response = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language
                )
            return response.text.strip()
        except Exception as e:
            logger.error(f"OpenAI transcription failed: {e}")
            raise TranscriptionError(f"OpenAI API error: {e}")


class LocalWhisperBackend(TranscriberBackend):
    """Local faster-whisper backend."""

    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self._model = None

    def _load_model(self):
        """Lazy load the model."""
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
                logger.info(f"Loading Whisper model: {self.model_size}")
                self._model = WhisperModel(
                    self.model_size,
                    device="auto",
                    compute_type="auto"
                )
                logger.info("Whisper model loaded")
            except Exception as e:
                logger.error(f"Failed to load Whisper model: {e}")
                raise TranscriptionError(f"Model loading error: {e}")

    def transcribe(self, audio_path: Path, language: str = "en") -> str:
        """Transcribe using local faster-whisper."""
        self._load_model()

        try:
            segments, info = self._model.transcribe(
                str(audio_path),
                language=language,
                beam_size=5
            )

            # Combine all segments
            text = " ".join(segment.text for segment in segments)
            return text.strip()
        except Exception as e:
            logger.error(f"Local transcription failed: {e}")
            raise TranscriptionError(f"Transcription error: {e}")


class TranscriptionError(Exception):
    """Exception raised when transcription fails."""
    pass


class Transcriber:
    """Main transcriber class that manages backends."""

    def __init__(
        self,
        mode: str = "openai",
        api_key: Optional[str] = None,
        model_size: str = "base"
    ):
        self.mode = mode
        self._backend: Optional[TranscriberBackend] = None

        if mode == "openai":
            if not api_key:
                raise ValueError("OpenAI API key required for OpenAI mode")
            self._backend = OpenAIWhisperBackend(api_key)
        elif mode == "local":
            self._backend = LocalWhisperBackend(model_size)
        else:
            raise ValueError(f"Unknown transcription mode: {mode}")

    def transcribe(self, audio_path: Path, language: str = "en") -> str:
        """Transcribe audio file to text."""
        if not audio_path.exists():
            raise TranscriptionError(f"Audio file not found: {audio_path}")

        result = self._backend.transcribe(audio_path, language)

        # Clean up temp file after transcription
        try:
            audio_path.unlink()
        except Exception as e:
            logger.warning(f"Failed to delete temp file: {e}")

        return result

    def set_mode(
        self,
        mode: str,
        api_key: Optional[str] = None,
        model_size: str = "base"
    ) -> None:
        """Change transcription mode."""
        self.mode = mode
        if mode == "openai":
            if not api_key:
                raise ValueError("OpenAI API key required for OpenAI mode")
            self._backend = OpenAIWhisperBackend(api_key)
        elif mode == "local":
            self._backend = LocalWhisperBackend(model_size)
        else:
            raise ValueError(f"Unknown transcription mode: {mode}")
