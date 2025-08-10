from __future__ import annotations
from typing import Optional, List
import os

from openai import OpenAI
import google.generativeai as genai

from .config import settings
from .prompts import build_system_prompt
from .specializations import LearningPath, DeliveryFormat
from .emotion_detection import emotion_detector


class LLMClient:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None) -> None:
        self.dev_fake = os.getenv("PROFAI_DEV_FAKE", "").lower() in {"1", "true", "yes"}
        
        # Determine which API to use
        self.use_gemini = settings.use_gemini
        
        if self.use_gemini:
            self.api_key = api_key or settings.gemini_api_key
            if not self.api_key and not self.dev_fake:
                raise RuntimeError(
                    "GEMINI_API_KEY not set. Please set environment variable GEMINI_API_KEY or enable PROFAI_DEV_FAKE."
                )
            if not self.dev_fake:
                genai.configure(api_key=self.api_key)
                self.model = model or settings.model or "gemini-1.5-flash"
                self.client = genai.GenerativeModel(self.model)
            else:
                self.client = None
        else:
            self.api_key = api_key or settings.openai_api_key
            if not self.api_key and not self.dev_fake:
                raise RuntimeError(
                    "OPENAI_API_KEY not set. Please set environment variable OPENAI_API_KEY or enable PROFAI_DEV_FAKE."
                )
            self.model = model or settings.model or "gpt-4o-mini"
            self.client = None if self.dev_fake else OpenAI(api_key=self.api_key)

    def generate(
        self, 
        user_text: str, 
        emotion: Optional[str] = None, 
        temperature: float = 0.3,
        learning_path: Optional[LearningPath] = None,
        delivery_format: Optional[DeliveryFormat] = None,
        lesson_id: Optional[str] = None,
        conversation_history: Optional[List[str]] = None,
        language: str = "en"
    ) -> str:
        """Generate educational response with specialization, emotion awareness, and multilingual support"""
        
        # Add language instruction to the user text
        language_instruction = self._get_language_instruction(language)
        enhanced_user_text = f"{language_instruction}\n\n{user_text}" if language != "en" else user_text
        
        # Build specialized system prompt
        system_prompt = build_system_prompt(
            user_text=enhanced_user_text,
            learning_path=learning_path,
            delivery_format=delivery_format,
            lesson_id=lesson_id,
            conversation_history=conversation_history,
            language=language
        )
        
        if self.dev_fake:
            return f"[FAKE ANSWER] {user_text} — here is a concise, clear explanation tailored to {emotion or 'neutral'} tone."
        
        try:
            if self.use_gemini:
                # Gemini API with improved settings for education
                if language != "en":
                    language_names = {
                        "es": "Spanish", "fr": "French", "de": "German", "it": "Italian", 
                        "pt": "Portuguese", "pl": "Polish", "hi": "Hindi", "ar": "Arabic",
                        "zh": "Chinese", "ja": "Japanese", "ko": "Korean"
                    }
                    lang_name = language_names.get(language, language)
                    prompt = f"{system_prompt}\n\nStudent Question: {user_text}\n\nIMPORTANT: Your response must be ENTIRELY in {lang_name}. Do not use English.\n\nProfAI Response in {lang_name}:"
                else:
                    prompt = f"{system_prompt}\n\nStudent Question: {user_text}\n\nProfAI Response:"
                
                generation_config = {
                    'temperature': temperature,
                    'max_output_tokens': 600,  # Slightly increased for educational content
                    'top_p': 0.8,
                    'top_k': 40
                }
                
                response = self.client.generate_content(
                    prompt,
                    generation_config=generation_config
                )
                
                # Handle the response properly
                if hasattr(response, 'text') and response.text:
                    return response.text.strip()
                elif hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts') and candidate.content.parts:
                            return candidate.content.parts[0].text.strip()
                
                return "I apologize, but I couldn't generate a response. Please try asking your question again."
            else:
                # OpenAI API with educational focus
                user_message = user_text
                if language != "en":
                    language_names = {
                        "es": "Spanish", "fr": "French", "de": "German", "it": "Italian", 
                        "pt": "Portuguese", "pl": "Polish", "hi": "Hindi", "ar": "Arabic",
                        "zh": "Chinese", "ja": "Japanese", "ko": "Korean"
                    }
                    lang_name = language_names.get(language, language)
                    user_message = f"{user_text}\n\nIMPORTANT: Please respond ENTIRELY in {lang_name}. Do not use English in your response."
                
                resp = self.client.chat.completions.create(  # type: ignore[union-attr]
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    temperature=temperature,
                    max_tokens=600,
                    top_p=0.8
                )
                return (resp.choices[0].message.content or "").strip()
        except Exception as e:
            print(f"Error in LLM generate: {e}")
            return "I'm having trouble processing your question right now. Please try again, or rephrase your question."

    def generate_lesson_content(
        self,
        lesson_id: str,
        learning_path: LearningPath,
        delivery_format: DeliveryFormat,
        user_question: Optional[str] = None
    ) -> str:
        """Generate structured lesson content for a specific lesson"""
        
        if user_question:
            prompt = f"Student is asking about lesson '{lesson_id}': {user_question}"
        else:
            prompt = f"Please teach the lesson '{lesson_id}' according to the curriculum."
        
        return self.generate(
            user_text=prompt,
            learning_path=learning_path,
            delivery_format=delivery_format,
            lesson_id=lesson_id,
            temperature=0.2  # Lower temperature for structured content
        )

    def assess_learning_progress(
        self,
        conversation_history: List[str],
        current_lesson: Optional[str] = None
    ) -> str:
        """Assess learner's progress and provide recommendations"""
        
        # Analyze emotional journey
        emotion_analysis = emotion_detector.analyze_conversation_emotion(conversation_history)
        
        assessment_prompt = (
            f"Based on our conversation, assess the learner's progress. "
            f"Current lesson: {current_lesson or 'General AI Discussion'}. "
            f"Detected emotional state: {emotion_analysis.primary_emotion.value}. "
            f"Provide: 1) Progress summary, 2) Areas of strength, 3) Areas for improvement, "
            f"4) Recommended next steps or lessons."
        )
        
        return self.generate(
            user_text=assessment_prompt,
            conversation_history=conversation_history,
            temperature=0.4
        )
    
    def _get_language_instruction(self, language: str) -> str:
        """Get language-specific instruction for the AI to respond in the target language"""
        language_names = {
            "en": "English",
            "es": "Spanish (Español)", 
            "fr": "French (Français)",
            "de": "German (Deutsch)",
            "it": "Italian (Italiano)",
            "pt": "Portuguese (Português)",
            "pl": "Polish (Polski)",
            "hi": "Hindi (हिन्दी)",
            "ar": "Arabic (العربية)",
            "zh": "Chinese (中文)",
            "ja": "Japanese (日本語)",
            "ko": "Korean (한국어)"
        }
        
        if language == "en":
            return ""  # No instruction needed for English
        
        language_name = language_names.get(language, language.upper())
        return f"Please respond in {language_name}. Provide a clear, educational explanation in {language_name}."


# Utility function for simple LLM responses
def get_llm_response(prompt: str, temperature: float = 0.3) -> str:
    """Simple utility function to get an LLM response"""
    try:
        client = LLMClient()
        response = client.generate(user_text=prompt, temperature=temperature)
        return response
    except Exception as e:
        print(f"Error generating LLM response: {e}")
        return "I apologize, but I couldn't generate a detailed explanation at the moment. Please try asking a specific question about what's confusing you."
