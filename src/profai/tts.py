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


def get_voice_settings_for_emotion(user_emotion: Optional[str], content_type: str = "explanation") -> Dict[str, Any]:
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

    def synthesize(self, text: str, voice: Optional[str] = None, play_audio: bool = True, user_emotion: Optional[str] = None) -> Path:
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

        v = (voice or self.voice or "Bella").strip()
        
        # Get emotion-based voice settings
        voice_settings = get_voice_settings_for_emotion(user_emotion)
        print(f"Using voice settings for emotion '{user_emotion}': {voice_settings}")
        
        # Retry logic for API calls
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"Generating TTS (attempt {attempt + 1}/{max_retries}) for filtered text length: {len(speech_text)} chars, voice: {v}, emotion: {user_emotion}")
                
                # Add a small delay between retries to avoid rate limiting
                if attempt > 0:
                    delay = random.uniform(1, 3)  # 1-3 seconds random delay
                    print(f"Waiting {delay:.1f} seconds before retry...")
                    time.sleep(delay)
                
                # Generate audio with emotion-based voice settings
                audio = self.client.generate(
                    text=speech_text, 
                    voice=v, 
                    model="eleven_turbo_v2",
                    voice_settings=voice_settings
                )
                save(audio, str(out_path))
                print(f"TTS audio saved successfully to: {out_path}")
                
                # Verify the file was created and has content
                if out_path.exists() and out_path.stat().st_size > 100:  # More than 100 bytes means real audio
                    print(f"Audio file size: {out_path.stat().st_size} bytes")
                    break  # Success, exit retry loop
                else:
                    print(f"Warning: Audio file is too small: {out_path.stat().st_size if out_path.exists() else 'file not found'}")
                    continue  # Try again
                    
            except Exception as e:
                print(f"Error generating TTS audio (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:  # Last attempt failed
                    print(f"All TTS attempts failed. Creating placeholder file: {out_path}")
                    # Create a tiny placeholder so pipeline completes when API fails
                    with open(out_path, "wb") as f:
                        f.write(b"PLACEHOLDER_MP3")
                    break
                else:
                    continue  # Try again

        if play_audio and out_path.exists() and out_path.stat().st_size > 100:
            try:
                play(audio)
            except Exception as e:
                print(f"Error playing audio: {e}")
                try:
                    if os.name == "nt":
                        os.startfile(str(out_path))  # type: ignore[attr-defined]
                except Exception as e2:
                    print(f"Error opening audio file: {e2}")
        return out_path
