from __future__ import annotations
from typing import Optional
import os
from pathlib import Path

from openai import OpenAI

from .config import settings


class STTClient:
    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or settings.openai_api_key
        self.dev_fake = os.getenv("PROFAI_DEV_FAKE", "").lower() in {"1", "true", "yes"}
        if not self.api_key and not self.dev_fake:
            raise RuntimeError(
                "OPENAI_API_KEY not set. Set OPENAI_API_KEY or enable PROFAI_DEV_FAKE."
            )
        self.client = None if self.dev_fake else OpenAI(api_key=self.api_key)

    def transcribe_file(self, file_path: str, model: str = "whisper-1") -> str:
        if self.dev_fake:
            return "[FAKE TRANSCRIPT] This is a placeholder transcription."
        p = Path(file_path)
        if not p.exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")
        with p.open("rb") as f:
            # OpenAI v1 Audio Transcriptions
            result = self.client.audio.transcriptions.create(
                model=model,
                file=f,
            )
            # result.text is the transcribed text
            return getattr(result, "text", "") or ""
