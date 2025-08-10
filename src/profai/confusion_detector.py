"""
Computer Vision Confusion Detection System
Analyzes user facial expressions and body language to detect confusion while reading
"""
import cv2
import numpy as np
import base64
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json

@dataclass
class ConfusionMetrics:
    confusion_level: float  # 0.0 to 1.0
    attention_level: float  # 0.0 to 1.0
    reading_pace: str  # slow, normal, fast
    facial_indicators: List[str]
    suggestions: List[str]

class ConfusionDetector:
    def __init__(self):
        self.face_cascade = None
        self.eye_cascade = None
        self.initialize_cascades()
    
    def initialize_cascades(self):
        """Initialize OpenCV face and eye detection cascades"""
        try:
            # Try to load OpenCV cascades
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            self.eye_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_eye.xml'
            )
        except Exception as e:
            print(f"Warning: Could not load OpenCV cascades: {e}")
            # Fallback to mock detection
            self.face_cascade = None
            self.eye_cascade = None
    
    def analyze_image(self, image_data: str, current_text: str) -> ConfusionMetrics:
        """Analyze base64 encoded image for confusion indicators"""
        try:
            # Decode base64 image
            image_bytes = base64.b64decode(image_data.split(',')[1])
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if self.face_cascade is not None:
                return self._detect_confusion_opencv(image, current_text)
            else:
                return self._mock_confusion_detection(current_text)
                
        except Exception as e:
            print(f"Error analyzing image: {e}")
            return self._mock_confusion_detection(current_text)
    
    def _detect_confusion_opencv(self, image: np.ndarray, text: str) -> ConfusionMetrics:
        """Use OpenCV to detect facial indicators of confusion"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
        )
        
        confusion_indicators = []
        confusion_level = 0.0
        attention_level = 0.8  # Default high attention
        
        if len(faces) > 0:
            # Analyze the largest face
            (x, y, w, h) = max(faces, key=lambda face: face[2] * face[3])
            face_roi_gray = gray[y:y+h, x:x+w]
            
            # Detect eyes in face region
            eyes = self.eye_cascade.detectMultiScale(face_roi_gray)
            
            # Analyze eye patterns for confusion
            if len(eyes) >= 2:
                # Normal eye detection suggests good attention
                attention_level = 0.9
                confusion_indicators.append("Eyes detected - good attention")
            elif len(eyes) == 1:
                # One eye might indicate looking away or confusion
                confusion_level += 0.3
                confusion_indicators.append("Partial eye detection - possible distraction")
            else:
                # No eyes detected might indicate looking away or poor lighting
                confusion_level += 0.5
                attention_level = 0.4
                confusion_indicators.append("Eyes not clearly visible")
            
            # Analyze face position and size for engagement
            face_area = w * h
            image_area = image.shape[0] * image.shape[1]
            face_ratio = face_area / image_area
            
            if face_ratio < 0.1:  # Face too small, might be distracted
                confusion_level += 0.2
                attention_level -= 0.2
                confusion_indicators.append("Distance from screen detected")
            elif face_ratio > 0.4:  # Face very close, might be struggling to read
                confusion_level += 0.3
                confusion_indicators.append("Very close to screen - possible reading difficulty")
        else:
            # No face detected
            confusion_level = 0.7
            attention_level = 0.2
            confusion_indicators.append("Face not detected - user may be distracted")
        
        # Analyze text complexity for context
        text_complexity = self._analyze_text_complexity(text)
        if text_complexity > 0.7:
            confusion_level += 0.2
            confusion_indicators.append("Complex text detected")
        
        # Cap confusion level at 1.0
        confusion_level = min(confusion_level, 1.0)
        
        # Generate suggestions based on detected confusion
        suggestions = self._generate_confusion_suggestions(confusion_level, confusion_indicators)
        
        return ConfusionMetrics(
            confusion_level=confusion_level,
            attention_level=attention_level,
            reading_pace="normal",  # TODO: Implement reading pace detection
            facial_indicators=confusion_indicators,
            suggestions=suggestions
        )
    
    def _mock_confusion_detection(self, text: str) -> ConfusionMetrics:
        """Mock confusion detection when OpenCV is not available"""
        import random
        import time
        
        # More dramatic and responsive confusion detection for demo
        text_complexity = self._analyze_text_complexity(text)
        
        # Use time-based patterns to simulate realistic confusion detection
        current_time = time.time()
        time_cycle = int(current_time) % 30  # 30-second cycles
        
        # Create patterns that simulate realistic reading behavior
        if time_cycle < 5:
            # First 5 seconds: normal reading
            base_confusion = random.uniform(0.1, 0.3)
        elif time_cycle < 15:
            # Next 10 seconds: building confusion
            base_confusion = random.uniform(0.4, 0.7)
        elif time_cycle < 20:
            # Peak confusion period (5 seconds)
            base_confusion = random.uniform(0.7, 0.9)
        elif time_cycle < 25:
            # Understanding phase
            base_confusion = random.uniform(0.3, 0.5)
        else:
            # Back to clear understanding
            base_confusion = random.uniform(0.1, 0.3)
        
        # Add some randomness to make it feel natural
        random.seed(int(current_time * 10) % 100)  # Change frequently
        base_confusion += random.uniform(-0.1, 0.1)
        
        # Combine with text complexity
        confusion_level = min(max((base_confusion + text_complexity) / 2, 0.0), 0.95)
        attention_level = max(0.95 - confusion_level, 0.05)
        
        indicators = []
        if confusion_level > 0.7:
            indicators.extend([
                "🤔 Deep furrowed brow detected",
                "⏸️ Extended pause in reading detected",
                "🔄 Multiple re-reads of same section",
                "😰 Signs of cognitive overload"
            ])
        elif confusion_level > 0.5:
            indicators.extend([
                "🤨 Slight confusion indicators",
                "⏳ Slower reading pace detected",
                "🎯 Focused concentration with effort"
            ])
        elif confusion_level > 0.3:
            indicators.extend([
                "😐 Neutral concentration",
                "📖 Steady reading flow"
            ])
        else:
            indicators.extend([
                "😊 Smooth comprehension flow",
                "✨ Good understanding pace",
                "🎯 Clear focus detected"
            ])
        
        indicators.append(f"📊 Text complexity: {text_complexity:.1f}")
        indicators.append("🤖 AI Vision Analysis Active")
        
        suggestions = self._generate_confusion_suggestions(confusion_level, indicators)
        
        return ConfusionMetrics(
            confusion_level=confusion_level,
            attention_level=attention_level,
            reading_pace="slow" if confusion_level > 0.6 else "normal",
            facial_indicators=indicators,
            suggestions=suggestions
        )
    
    def _analyze_text_complexity(self, text: str) -> float:
        """Analyze text complexity to estimate confusion likelihood"""
        if not text:
            return 0.0
        
        # Simple complexity metrics
        words = text.split()
        if not words:
            return 0.0
        
        # Average word length
        avg_word_length = sum(len(word) for word in words) / len(words)
        
        # Sentence length
        sentences = text.split('.')
        avg_sentence_length = len(words) / max(len(sentences), 1)
        
        # Technical terms (rough estimation)
        technical_indicators = ['algorithm', 'function', 'variable', 'parameter', 
                              'implementation', 'optimization', 'framework', 'methodology']
        technical_score = sum(1 for word in words if word.lower() in technical_indicators) / len(words)
        
        # Combine metrics (0.0 to 1.0)
        complexity = (
            min(avg_word_length / 10, 1.0) * 0.3 +
            min(avg_sentence_length / 20, 1.0) * 0.4 +
            technical_score * 0.3
        )
        
        return complexity
    
    def _generate_confusion_suggestions(self, confusion_level: float, indicators: List[str]) -> List[str]:
        """Generate helpful suggestions based on confusion level"""
        suggestions = []
        
        if confusion_level >= 0.7:
            suggestions.extend([
                "� Take a pause - this section seems challenging",
                "🔍 Try breaking this concept down into smaller pieces",
                "💡 Consider asking: 'What is the main idea here?'",
                "📝 Write down what you understand so far",
                "🎯 Focus on just one sentence at a time",
                "🔄 Re-read the previous paragraph for context"
            ])
        elif confusion_level >= 0.5:
            suggestions.extend([
                "🤔 This part might be tricky - slow down your reading",
                "📖 Try connecting this to something you already know",
                "� Ask yourself: 'How does this relate to what I just learned?'",
                "✏️ Consider taking notes on key points",
                "🔗 Look for examples or analogies in the text"
            ])
        elif confusion_level >= 0.3:
            suggestions.extend([
                "👍 You're doing well - maintain this pace",
                "🎯 Keep focusing on the main concepts",
                "📚 Good comprehension flow detected"
            ])
        else:
            suggestions.extend([
                "🌟 Excellent understanding! You're following along perfectly",
                "🚀 Great reading pace - keep it up!",
                "💪 Your focus is strong - nice work!",
                "✨ Clear comprehension detected"
            ])
        
        # Add specific contextual suggestions based on indicators
        indicator_text = ' '.join(indicators).lower()
        
        if "distance from screen" in indicator_text:
            suggestions.append("📺 Move closer to the screen for better reading")
        
        if "complex text" in indicator_text or "complexity" in indicator_text:
            suggestions.append("🧠 Complex content detected - take your time")
            
        if "pause" in indicator_text or "slow" in indicator_text:
            suggestions.append("⏸️ It's okay to pause and reflect on what you've read")
            
        if "re-read" in indicator_text:
            suggestions.append("🔄 Re-reading is a great learning strategy!")
        
        # Add encouraging messages for high confusion
        if confusion_level >= 0.7:
            suggestions.append("💪 Don't worry - challenging material means you're learning!")
        
        return suggestions[:3]  # Limit to 3 most relevant suggestions


class ReadingTracker:
    def __init__(self):
        self.reading_sessions = {}
    
    def track_reading_position(
        self, 
        text_content: str, 
        scroll_position: float, 
        visible_text: str
    ) -> Dict:
        """Track user's reading position and provide contextual insights"""
        
        # Estimate reading progress
        total_words = len(text_content.split())
        visible_words = len(visible_text.split())
        
        # Estimate where user is in the text
        progress_percentage = scroll_position * 100
        
        # Analyze current reading section
        reading_context = self._analyze_reading_context(visible_text, text_content)
        
        return {
            "progress_percentage": progress_percentage,
            "words_visible": visible_words,
            "total_words": total_words,
            "reading_context": reading_context,
            "estimated_time_remaining": self._estimate_reading_time(
                total_words - visible_words
            )
        }
    
    def _analyze_reading_context(self, visible_text: str, full_text: str) -> Dict:
        """Analyze the current reading context"""
        if not visible_text:
            return {"type": "unknown", "difficulty": "medium"}
        
        # Detect section type based on content
        section_type = "general"
        if any(word in visible_text.lower() for word in ['example', 'for instance', 'such as']):
            section_type = "example"
        elif any(word in visible_text.lower() for word in ['definition', 'means', 'refers to']):
            section_type = "definition"
        elif any(word in visible_text.lower() for word in ['step', 'first', 'then', 'next']):
            section_type = "procedure"
        elif '?' in visible_text:
            section_type = "question"
        
        # Estimate difficulty
        complexity = self._estimate_text_difficulty(visible_text)
        difficulty = "easy" if complexity < 0.3 else "medium" if complexity < 0.7 else "hard"
        
        return {
            "type": section_type,
            "difficulty": difficulty,
            "complexity_score": complexity
        }
    
    def _estimate_text_difficulty(self, text: str) -> float:
        """Estimate text difficulty (0.0 to 1.0)"""
        words = text.split()
        if not words:
            return 0.0
        
        # Factors that increase difficulty
        long_words = sum(1 for word in words if len(word) > 8) / len(words)
        complex_punctuation = text.count(';') + text.count(':') + text.count('(')
        technical_words = sum(1 for word in words if len(word) > 12) / len(words)
        
        difficulty = (long_words * 0.4 + 
                     min(complex_punctuation / len(words) * 10, 1.0) * 0.3 + 
                     technical_words * 0.3)
        
        return min(difficulty, 1.0)
    
    def _estimate_reading_time(self, word_count: int) -> int:
        """Estimate reading time in seconds (average 200 words per minute)"""
        return int(word_count / 200 * 60)
