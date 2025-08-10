import os
from dataclasses import dataclass
from dotenv import load_dotenv
from pathlib import Path

# Load environment from .env file in the root directory
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)


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
    
    # Cost-saving features
    cost_saving_mode: bool = os.getenv("PROFAI_COST_SAVING_MODE", "0") == "1"
    disable_auto_tts: bool = os.getenv("PROFAI_DISABLE_AUTO_TTS", "0") == "1"
    multilingual_only_when_needed: bool = os.getenv("PROFAI_MULTILINGUAL_ONLY_WHEN_NEEDED", "0") == "1"
    dev_fake: bool = os.getenv("PROFAI_DEV_FAKE", "0") == "1"


settings = Settings()
