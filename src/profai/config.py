import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment from .env if present
load_dotenv()


@dataclass
class Settings:
    # Support both OpenAI and Gemini
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY")
    elevenlabs_api_key: str | None = os.getenv("ELEVENLABS_API_KEY")
    elevenlabs_voice: str = os.getenv("ELEVENLABS_VOICE", "Bella")  # default voice name
    
    # Model configuration
    model: str = os.getenv("GEMINI_MODEL") or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    use_gemini: bool = bool(os.getenv("GEMINI_API_KEY"))  # Auto-detect based on key presence


settings = Settings()
