from __future__ import annotations
import os
import time
from pathlib import Path
from typing import Optional

from elevenlabs import save, play
from elevenlabs.client import ElevenLabs

from .config import settings


OUTPUT_DIR = Path(__file__).resolve().parents[2] / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class TTSClient:
    def __init__(self, api_key: Optional[str] = None, default_voice: Optional[str] = None) -> None:
        self.api_key = api_key or settings.elevenlabs_api_key
        self.dev_fake = os.getenv("PROFAI_DEV_FAKE", "").lower() in {"1", "true", "yes"}
        self.disabled = os.getenv("PROFAI_TTS_DISABLED", "").lower() in {"1", "true", "yes"}
        if not self.api_key and not (self.dev_fake or self.disabled):
            raise RuntimeError(
                "ELEVENLABS_API_KEY not set. Please set environment variable ELEVENLABS_API_KEY or enable PROFAI_DEV_FAKE."
            )
        self.voice = (default_voice or settings.elevenlabs_voice).strip()
        self.client = None if (self.dev_fake or self.disabled) else ElevenLabs(api_key=self.api_key)

    def synthesize(self, text: str, voice: Optional[str] = None, play_audio: bool = True) -> str:
        ts = int(time.time() * 1000)
        out_path = OUTPUT_DIR / f"profai_{ts}.mp3"
        if self.dev_fake or self.disabled:
            # Create a tiny placeholder so pipeline completes when disabled/fake
            with open(out_path, "wb") as f:
                f.write(b"PLACEHOLDER_MP3")
            if play_audio and os.name == "nt" and not self.disabled:
                try:
                    os.startfile(str(out_path))  # type: ignore[attr-defined]
                except Exception:
                    pass
            return str(out_path)

        v = (voice or self.voice or "Bella").strip()
        audio = self.client.generate(text=text, voice=v, model="eleven_turbo_v2")
        save(audio, str(out_path))

        if play_audio:
            try:
                play(audio)
            except Exception:
                try:
                    if os.name == "nt":
                        os.startfile(str(out_path))  # type: ignore[attr-defined]
                except Exception:
                    pass
        return str(out_path)
