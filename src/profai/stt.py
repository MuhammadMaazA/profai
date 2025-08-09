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

    def transcribe_file(self, file_path: str, model: str = "whisper-1", language: Optional[str] = None) -> dict:
        """Transcribe audio file and detect language if not specified"""
        if self.dev_fake:
            return {
                "text": "[FAKE TRANSCRIPT] This is a placeholder transcription.",
                "language": language or "en"
            }
            
        p = Path(file_path)
        if not p.exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")
            
        if self.use_openai:
            # Use OpenAI Whisper with language detection
            with p.open("rb") as f:
                try:
                    if language:
                        # Transcribe with specified language
                        result = self.client.audio.transcriptions.create(
                            model=model,
                            file=f,
                            language=language
                        )
                    else:
                        # Let Whisper detect language automatically
                        result = self.client.audio.transcriptions.create(
                            model=model,
                            file=f,
                        )
                    
                    text = getattr(result, "text", "") or ""
                    # Whisper automatically detects language, we can try to detect it from the result
                    detected_language = self._detect_language_from_text(text) if not language else language
                    
                    return {
                        "text": text.strip(),
                        "language": detected_language
                    }
                except Exception as e:
                    print(f"STT: OpenAI error: {str(e)}")
                    raise e
        else:
            # Use speech_recognition library with Google Web Speech API (free)
            try:
                with sr.AudioFile(str(p)) as source:
                    audio = self.recognizer.record(source)
                    # Google Speech Recognition supports language hints
                    lang_code = language if language else "en-US"
                    text = self.recognizer.recognize_google(audio, language=lang_code)
                    detected_language = language[:2] if language else "en"
                    return {
                        "text": text.strip(),
                        "language": detected_language
                    }
            except sr.UnknownValueError:
                return {
                    "text": "Could not understand audio",
                    "language": language or "en"
                }
            except sr.RequestError as e:
                raise RuntimeError(f"Speech recognition error: {e}")
            except Exception as e:
                raise RuntimeError(f"Error processing audio file: {e}")
    
    def _detect_language_from_text(self, text: str) -> str:
        """Simple language detection based on text characteristics"""
        # This is a basic implementation - you could use a proper language detection library
        # For now, we'll use simple heuristics
        text_lower = text.lower()
        
        # Spanish indicators
        if any(word in text_lower for word in ["qué", "cómo", "cuándo", "dónde", "por qué", "el", "la", "de", "en", "y"]):
            return "es"
        
        # French indicators  
        if any(word in text_lower for word in ["qu'est-ce", "comment", "quand", "où", "pourquoi", "le", "la", "de", "en", "et"]):
            return "fr"
        
        # German indicators
        if any(word in text_lower for word in ["was", "wie", "wann", "wo", "warum", "der", "die", "das", "und", "ich", "ist"]):
            return "de"
        
        # Default to English
        return "en"
