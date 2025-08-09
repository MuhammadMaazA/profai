import os
from dataclasses import dataclass


@dataclass
class Settings:
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    elevenlabs_api_key: str | None = os.getenv("ELEVENLABS_API_KEY")
    elevenlabs_voice: str = os.getenv("ELEVENLABS_VOICE", "Bella")  # default voice name
    model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


settings = Settings()
