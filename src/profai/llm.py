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
        conversation_history: Optional[List[str]] = None
    ) -> str:
        """Generate educational response with specialization and emotion awareness"""
        
        # Build specialized system prompt
        system_prompt = build_system_prompt(
            user_text=user_text,
            learning_path=learning_path,
            delivery_format=delivery_format,
            lesson_id=lesson_id,
            conversation_history=conversation_history
        )
        
        if self.dev_fake:
            return f"[FAKE ANSWER] {user_text} — here is a concise, clear explanation tailored to {emotion or 'neutral'} tone."
        
        try:
            if self.use_gemini:
                # Gemini API with improved settings for education
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
                resp = self.client.chat.completions.create(  # type: ignore[union-attr]
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_text},
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
