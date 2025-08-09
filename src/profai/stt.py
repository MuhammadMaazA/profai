from __future__ import annotations
from typing import Optional
import os
from pathlib import Path

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False

from .config import settings


class STTClient:
    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or settings.openai_api_key
        self.dev_fake = os.getenv("PROFAI_DEV_FAKE", "").lower() in {"1", "true", "yes"}
        
        # Check if we have OpenAI key and library
        self.use_openai = bool(self.api_key and self.api_key != "your_openai_api_key" and OPENAI_AVAILABLE)
        
        if not self.use_openai and not SPEECH_RECOGNITION_AVAILABLE and not self.dev_fake:
            raise RuntimeError(
                "Neither OpenAI API key nor speech_recognition library available. "
                "Either set OPENAI_API_KEY, install speech_recognition, or enable PROFAI_DEV_FAKE."
            )
        
        self.client = None if (self.dev_fake or not self.use_openai) else OpenAI(api_key=self.api_key)
        
        if not self.use_openai and not self.dev_fake:
            # Initialize speech recognition
            self.recognizer = sr.Recognizer()

    def transcribe_file(self, file_path: str, model: str = "whisper-1") -> str:
        if self.dev_fake:
            return "[FAKE TRANSCRIPT] This is a placeholder transcription."
            
        p = Path(file_path)
        if not p.exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")
            
        if self.use_openai:
            # Use OpenAI Whisper
            with p.open("rb") as f:
                try:
                    result = self.client.audio.transcriptions.create(
                        model=model,
                        file=f,
                    )
                    text = getattr(result, "text", "") or ""
                    return text.strip()
                except Exception as e:
                    print(f"STT: OpenAI error: {str(e)}")
                    raise e
        else:
            # Use speech_recognition library with Google Web Speech API (free)
            try:
                with sr.AudioFile(str(p)) as source:
                    audio = self.recognizer.record(source)
                    text = self.recognizer.recognize_google(audio)
                    return text.strip()
            except sr.UnknownValueError:
                return "Could not understand audio"
            except sr.RequestError as e:
                raise RuntimeError(f"Speech recognition error: {e}")
            except Exception as e:
                raise RuntimeError(f"Error processing audio file: {e}")
