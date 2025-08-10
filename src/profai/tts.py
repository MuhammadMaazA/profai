from __future__ import annotations
import os
import time
import re
from pathlib import Path
from typing import Optional, Dict, Any
import random

from elevenlabs import save, play
from elevenlabs.client import ElevenLabs

from .config import settings


OUTPUT_DIR = Path(__file__).resolve().parents[2] / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_multilingual_voice_and_model(language: str = "en") -> Dict[str, str]:
    """
    Returns appropriate voice and model for different languages with cost optimization.
    ElevenLabs supports multilingual voices and models.
    """
    from .config import settings
    
    # Cost-saving: Use cheaper monolingual model for English when in cost-saving mode
    if settings.cost_saving_mode and language == "en":
        return {
            "voice": "21m00Tcm4TlvDq8ikWAM",
            "model": "eleven_monolingual_v1"  # Cheaper for English-only
        }
    
    # Smart multilingual: Only use expensive multilingual when actually needed
    if settings.multilingual_only_when_needed and language == "en":
        return {
            "voice": "21m00Tcm4TlvDq8ikWAM", 
            "model": "eleven_monolingual_v1"
        }
    
    # Language-specific voice configurations
    voice_configs = {
        "en": {  # English
            "voice": "21m00Tcm4TlvDq8ikWAM",  # Default voice (Rachel/Bella)
            "model": "eleven_multilingual_v2"
        },
        "es": {  # Spanish
            "voice": "21m00Tcm4TlvDq8ikWAM",  # Same voice works for Spanish
            "model": "eleven_multilingual_v2"
        },
        "fr": {  # French
            "voice": "21m00Tcm4TlvDq8ikWAM",
            "model": "eleven_multilingual_v2"
        },
        "de": {  # German
            "voice": "21m00Tcm4TlvDq8ikWAM",
            "model": "eleven_multilingual_v2"
        },
        "it": {  # Italian
            "voice": "21m00Tcm4TlvDq8ikWAM",
            "model": "eleven_multilingual_v2"
        },
        "pt": {  # Portuguese
            "voice": "21m00Tcm4TlvDq8ikWAM",
            "model": "eleven_multilingual_v2"
        },
        "pl": {  # Polish
            "voice": "21m00Tcm4TlvDq8ikWAM",
            "model": "eleven_multilingual_v2"
        },
        "hi": {  # Hindi
            "voice": "21m00Tcm4TlvDq8ikWAM",
            "model": "eleven_multilingual_v2"
        },
        "ar": {  # Arabic
            "voice": "21m00Tcm4TlvDq8ikWAM",
            "model": "eleven_multilingual_v2"
        },
        "zh": {  # Chinese
            "voice": "21m00Tcm4TlvDq8ikWAM",
            "model": "eleven_multilingual_v2"
        },
        "ja": {  # Japanese
            "voice": "21m00Tcm4TlvDq8ikWAM",
            "model": "eleven_multilingual_v2"
        },
        "ko": {  # Korean
            "voice": "21m00Tcm4TlvDq8ikWAM",
            "model": "eleven_multilingual_v2"
        }
    }
    
    return voice_configs.get(language, voice_configs["en"])


def get_voice_settings_for_emotion(user_emotion: Optional[str], content_type: str = "explanation") -> Dict[str, Any]:
    """
    Get voice settings based on detected emotion with cost optimization.
    Simplified settings to reduce API complexity and costs.
    """
    from .config import settings
    
    # In cost-saving mode, use simplified voice settings
    if settings.cost_saving_mode:
        return {
            'stability': 0.4,  # Standard stability
            'similarity_boost': 0.7,  # Standard similarity
            'style': 0.2,  # Minimal style changes
            'use_speaker_boost': True
        }
    
    # Emotion-based voice adjustments (original complexity)
    base_settings = {
        'stability': 0.3,
        'similarity_boost': 0.75,
        'style': 0.4,
        'use_speaker_boost': True
    }
    
    if not user_emotion:
        return base_settings
    
    # Simplified emotion mapping for cost-saving
    emotion_adjustments = {
        'excited': {'stability': 0.2, 'style': 0.6},
        'calm': {'stability': 0.5, 'style': 0.2},
        'confused': {'stability': 0.4, 'style': 0.3},
        'frustrated': {'stability': 0.3, 'style': 0.4},
        'engaged': {'stability': 0.3, 'style': 0.4},
    }
    
    # Apply emotion adjustments
    adjustments = emotion_adjustments.get(user_emotion.lower(), {})
    final_settings = {**base_settings, **adjustments}
    
    return final_settings
    """
    Returns ElevenLabs voice settings based on user emotion and content type.
    This makes the AI respond with appropriate tone like a human teacher would.
    """
    # Default settings for neutral/confident tone
    base_settings = {
        "stability": 0.5,
        "similarity_boost": 0.8,
        "style": 0.2,
        "use_speaker_boost": True
    }
    
    if not user_emotion:
        return base_settings
    
    # Adjust voice settings based on user's emotional state
    emotion_adjustments = {
        "confused": {
            "stability": 0.7,      # More stable, reassuring
            "similarity_boost": 0.9,
            "style": 0.1,          # Less expressive, more clear
            "use_speaker_boost": True
        },
        "frustrated": {
            "stability": 0.8,      # Very stable, calm
            "similarity_boost": 0.85,
            "style": 0.05,         # Minimal style, very patient
            "use_speaker_boost": True
        },
        "engaged": {
            "stability": 0.3,      # More dynamic
            "similarity_boost": 0.75,
            "style": 0.4,          # More expressive and enthusiastic
            "use_speaker_boost": True
        },
        "bored": {
            "stability": 0.4,      # Slightly more animated
            "similarity_boost": 0.8,
            "style": 0.3,          # More engaging tone
            "use_speaker_boost": True
        },
        "overwhelmed": {
            "stability": 0.9,      # Very stable, gentle
            "similarity_boost": 0.9,
            "style": 0.0,          # Minimal expression, very gentle
            "use_speaker_boost": True
        },
        "curious": {
            "stability": 0.4,      # Dynamic and encouraging
            "similarity_boost": 0.8,
            "style": 0.35,         # Encouraging and warm
            "use_speaker_boost": True
        },
        "confident": {
            "stability": 0.5,      # Balanced
            "similarity_boost": 0.8,
            "style": 0.25,         # Confident but not overwhelming
            "use_speaker_boost": True
        }
    }
    
    # Get emotion-specific settings, fallback to base if not found
    emotion_key = user_emotion.lower() if user_emotion else "confident"
    settings_override = emotion_adjustments.get(emotion_key, base_settings)
    
    return settings_override


def extract_speech_text(text: str) -> str:
    """
    Extract only the explanatory text from a response, excluding code blocks.
    This ensures that TTS only reads the educational content, not the code.
    """
    # Remove code blocks (both ``` and single backticks)
    # Remove triple backtick code blocks
    text = re.sub(r'```[\s\S]*?```', '', text, flags=re.MULTILINE)
    
    # Remove inline code (single backticks)
    text = re.sub(r'`[^`]*`', '', text)
    
    # Remove any remaining technical formatting
    # Remove lines that look like imports or variable assignments
    lines = text.split('\n')
    filtered_lines = []
    
    for line in lines:
        line = line.strip()
        # Skip lines that look like code
        if (line.startswith(('import ', 'from ', 'def ', 'class ', 'if ', 'for ', 'while ')) or
            '=' in line and not line.endswith('?') or
            line.startswith(('#', '//', '/*')) or
            line.endswith((';', '{', '}')) or
            not line):
            continue
        filtered_lines.append(line)
    
    # Join back and clean up extra whitespace
    result = ' '.join(filtered_lines)
    result = re.sub(r'\s+', ' ', result).strip()
    
    # If the result is too short, fall back to basic code block removal only
    if len(result) < 50:
        # Just remove code blocks but keep other text
        result = re.sub(r'```[\s\S]*?```', '', text, flags=re.MULTILINE)
        result = re.sub(r'`[^`]*`', '', result)
        result = re.sub(r'\s+', ' ', result).strip()
    
    print(f"TTS text filtering: {len(text)} chars -> {len(result)} chars")
    return result


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

    def synthesize(self, text: str, voice: Optional[str] = None, play_audio: bool = True, user_emotion: Optional[str] = None, language: str = "en") -> Path:
        # Filter out code blocks and keep only explanatory text for TTS
        speech_text = extract_speech_text(text)
        
        # If filtered text is too short, don't generate audio
        if len(speech_text.strip()) < 20:
            print("Filtered text too short for TTS, creating placeholder")
            ts = int(time.time() * 1000)
            out_path = OUTPUT_DIR / f"profai_{ts}.mp3"
            with open(out_path, "wb") as f:
                f.write(b"PLACEHOLDER_MP3")
            return out_path
        
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
            return out_path

        # Get language-specific voice and model configuration
        lang_config = get_multilingual_voice_and_model(language)
        selected_voice = voice or lang_config["voice"] or self.voice or "Bella"
        model = lang_config["model"]
        
        # Get emotion-based voice settings
        voice_settings = get_voice_settings_for_emotion(user_emotion)
        
        print(f"TTS Debug - Language: {language}, Voice: {selected_voice}, Model: {model}")
        print(f"TTS Debug - Voice Settings: {voice_settings}")
        print(f"TTS Debug - Speech text length: {len(speech_text)} chars")
        
        # Retry logic for ElevenLabs API reliability
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                print(f"TTS Attempt {attempt + 1}/{max_attempts}: Generating audio...")
                
                # Generate audio with multilingual model and emotion-based settings
                audio = self.client.generate(
                    text=speech_text,
                    voice=selected_voice,
                    model=model,
                    voice_settings=voice_settings
                )
                
                # Save the audio
                save(audio, str(out_path))
                
                # Verify file was created and has reasonable size
                if out_path.exists() and out_path.stat().st_size > 100:
                    print(f"TTS Success: Generated {out_path.stat().st_size} bytes")
                    if play_audio:
                        try:
                            play(audio)
                        except Exception:
                            try:
                                if os.name == "nt":
                                    os.startfile(str(out_path))  # type: ignore[attr-defined]
                            except Exception:
                                pass
                    return out_path
                else:
                    print(f"TTS Warning: File too small ({out_path.stat().st_size if out_path.exists() else 0} bytes)")
                    
            except Exception as e:
                print(f"TTS Attempt {attempt + 1} failed: {e}")
                if attempt < max_attempts - 1:
                    delay = random.uniform(1, 3)  # Random delay between retries
                    print(f"Retrying in {delay:.1f} seconds...")
                    time.sleep(delay)
                else:
                    print("All TTS attempts failed, creating placeholder")
        
        # If all attempts failed, create a placeholder file
        with open(out_path, "wb") as f:
            f.write(b"PLACEHOLDER_MP3")
        
        return out_path
