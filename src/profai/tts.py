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
        if not self.api_key:
            raise RuntimeError(
                "ELEVENLABS_API_KEY not set. Please set environment variable ELEVENLABS_API_KEY."
            )
        self.voice = (default_voice or settings.elevenlabs_voice).strip()
        self.client = ElevenLabs(api_key=self.api_key)

    def synthesize(self, text: str, voice: Optional[str] = None, play_audio: bool = True) -> str:
        v = (voice or self.voice or "Bella").strip()
        audio = self.client.generate(text=text, voice=v, model="eleven_turbo_v2")

        ts = int(time.time() * 1000)
        out_path = OUTPUT_DIR / f"profai_{ts}.mp3"
        save(audio, str(out_path))

        if play_audio:
            try:
                # Try SDK playback first (cross-platform)
                play(audio)
            except Exception:
                # Fallback: on Windows, open via default player
                try:
                    if os.name == "nt":
                        os.startfile(str(out_path))  # type: ignore[attr-defined]
                except Exception:
                    pass
        return str(out_path)
