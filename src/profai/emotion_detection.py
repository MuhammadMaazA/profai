"""
Advanced Emotion Detection for ProfAI
Detects learner emotional state and adapts teaching accordingly
"""
from __future__ import annotations
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re


class EmotionState(Enum):
    CONFUSED = "confused"
    FRUSTRATED = "frustrated"
    ENGAGED = "engaged"
    BORED = "bored"
    CONFIDENT = "confident"
    OVERWHELMED = "overwhelmed"
    CURIOUS = "curious"


@dataclass
class EmotionAnalysis:
    primary_emotion: EmotionState
    confidence: float
    indicators: List[str]
    teaching_adjustment: str


class EmotionDetector:
    def __init__(self):
        # Keywords and phrases that indicate different emotional states
        self.emotion_indicators = {
            EmotionState.CONFUSED: [
                "i don't understand", "what does that mean", "can you explain",
                "i'm lost", "confusing", "unclear", "what", "huh", "?",
                "i don't get it", "makes no sense", "can you repeat",
                "i'm confused", "don't follow", "clarify"
            ],
            EmotionState.FRUSTRATED: [
                "this is hard", "difficult", "impossible", "can't do this",
                "giving up", "frustrated", "annoying", "stupid", "hate this",
                "why won't this work", "nothing works", "fed up", "argh",
                "this sucks", "waste of time", "too complicated"
            ],
            EmotionState.ENGAGED: [
                "interesting", "cool", "awesome", "love this", "fascinating",
                "tell me more", "what about", "how about", "can we also",
                "that's great", "amazing", "wow", "nice", "excellent",
                "i want to learn", "show me", "teach me"
            ],
            EmotionState.BORED: [
                "boring", "tired", "sleepy", "uninteresting", "dull",
                "when will this end", "moving on", "skip this", "already know",
                "yawn", "whatever", "okay", "sure", "fine", "meh"
            ],
            EmotionState.CONFIDENT: [
                "i understand", "got it", "makes sense", "easy", "simple",
                "i know this", "obvious", "of course", "exactly", "yes",
                "perfect", "clear", "ready for more", "next", "bring it on"
            ],
            EmotionState.OVERWHELMED: [
                "too much", "too fast", "slow down", "overwhelming", "complex",
                "too many things", "information overload", "can't keep up",
                "too advanced", "need a break", "head spinning", "dizzy"
            ],
            EmotionState.CURIOUS: [
                "why", "how", "what if", "interesting", "tell me more",
                "can you explain", "what about", "how does", "why does",
                "curious", "wonder", "explore", "dive deeper", "learn more"
            ]
        }
        
        # Teaching adjustments for each emotion
        self.teaching_adjustments = {
            EmotionState.CONFUSED: (
                "Slow down, use simpler language, provide concrete examples, "
                "break down into smaller steps, ask comprehension questions"
            ),
            EmotionState.FRUSTRATED: (
                "Be encouraging and patient, acknowledge the difficulty, "
                "provide reassurance, offer alternative explanations, take breaks"
            ),
            EmotionState.ENGAGED: (
                "Maintain energy, provide additional details, offer challenges, "
                "encourage exploration, build on their enthusiasm"
            ),
            EmotionState.BORED: (
                "Add variety, use interactive elements, relate to interests, "
                "increase pace, provide real-world applications"
            ),
            EmotionState.CONFIDENT: (
                "Increase difficulty slightly, provide advanced topics, "
                "encourage teaching others, offer challenging problems"
            ),
            EmotionState.OVERWHELMED: (
                "Reduce information density, slow down pace, summarize key points, "
                "provide clear structure, offer breaks"
            ),
            EmotionState.CURIOUS: (
                "Encourage questions, provide deeper explanations, "
                "offer related topics, support exploration"
            )
        }

    def analyze_text_emotion(self, text: str) -> EmotionAnalysis:
        """Analyze emotion from text input"""
        text_lower = text.lower()
        
        # Count indicators for each emotion
        emotion_scores = {}
        detected_indicators = {}
        
        for emotion, indicators in self.emotion_indicators.items():
            score = 0
            found_indicators = []
            
            for indicator in indicators:
                if indicator in text_lower:
                    score += 1
                    found_indicators.append(indicator)
            
            emotion_scores[emotion] = score
            detected_indicators[emotion] = found_indicators
        
        # Find the emotion with the highest score
        if not any(emotion_scores.values()):
            # Default to engaged if no clear emotion detected
            primary_emotion = EmotionState.ENGAGED
            confidence = 0.3
            indicators = []
        else:
            primary_emotion = max(emotion_scores, key=emotion_scores.get)
            max_score = emotion_scores[primary_emotion]
            total_words = len(text.split())
            confidence = min(max_score / max(total_words, 1), 1.0)
            indicators = detected_indicators[primary_emotion]
        
        return EmotionAnalysis(
            primary_emotion=primary_emotion,
            confidence=confidence,
            indicators=indicators,
            teaching_adjustment=self.teaching_adjustments[primary_emotion]
        )

    def analyze_conversation_emotion(self, messages: List[str]) -> EmotionAnalysis:
        """Analyze emotion from a conversation history"""
        if not messages:
            return EmotionAnalysis(
                primary_emotion=EmotionState.ENGAGED,
                confidence=0.5,
                indicators=[],
                teaching_adjustment=self.teaching_adjustments[EmotionState.ENGAGED]
            )
        
        # Analyze recent messages with more weight on newer ones
        emotion_scores = {emotion: 0 for emotion in EmotionState}
        all_indicators = []
        
        for i, message in enumerate(messages[-5:]):  # Last 5 messages
            analysis = self.analyze_text_emotion(message)
            weight = (i + 1) / 5  # More weight for recent messages
            emotion_scores[analysis.primary_emotion] += analysis.confidence * weight
            all_indicators.extend(analysis.indicators)
        
        primary_emotion = max(emotion_scores, key=emotion_scores.get)
        confidence = emotion_scores[primary_emotion] / len(messages[-5:])
        
        return EmotionAnalysis(
            primary_emotion=primary_emotion,
            confidence=confidence,
            indicators=all_indicators,
            teaching_adjustment=self.teaching_adjustments[primary_emotion]
        )

    def get_adaptive_prompt_modifier(self, emotion: EmotionState) -> str:
        """Get prompt modification based on detected emotion"""
        modifiers = {
            EmotionState.CONFUSED: (
                "The learner seems confused. Use very simple language, provide step-by-step explanations, "
                "use concrete examples, and check understanding frequently. Avoid jargon."
            ),
            EmotionState.FRUSTRATED: (
                "The learner appears frustrated. Be extra encouraging and patient. "
                "Acknowledge that this is challenging and break things down into very small, manageable steps. "
                "Use reassuring language like 'This is normal to find difficult' or 'Let's work through this together.'"
            ),
            EmotionState.ENGAGED: (
                "The learner is engaged and interested. Maintain good energy, provide rich details, "
                "and feel free to go slightly deeper into the topic."
            ),
            EmotionState.BORED: (
                "The learner seems bored or disengaged. Make the content more interesting with "
                "real-world examples, interactive elements, or surprising facts. Vary your teaching style."
            ),
            EmotionState.CONFIDENT: (
                "The learner appears confident and ready for more. You can increase the difficulty slightly "
                "and provide more advanced concepts or challenging questions."
            ),
            EmotionState.OVERWHELMED: (
                "The learner seems overwhelmed. Simplify significantly, reduce the amount of information, "
                "and focus on just the most essential points. Use very clear structure and summarize frequently."
            ),
            EmotionState.CURIOUS: (
                "The learner is curious and asking good questions. Encourage this curiosity, "
                "provide detailed explanations, and offer related topics they might find interesting."
            )
        }
        return modifiers.get(emotion, modifiers[EmotionState.ENGAGED])


# Global emotion detector instance
emotion_detector = EmotionDetector()
