from __future__ import annotations
from typing import Dict, List, Optional, Any
from enum import Enum
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime


class EmotionalState(Enum):
    CONFUSED = "confused"
    FRUSTRATED = "frustrated"
    EXCITED = "excited"
    CONFIDENT = "confident"
    OVERWHELMED = "overwhelmed"
    CURIOUS = "curious"
    NEUTRAL = "neutral"


class LearningStyle(Enum):
    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    MIXED = "mixed"


@dataclass
class LearnerProfile:
    """Track learner's progress and preferences"""
    user_id: str
    name: Optional[str] = None
    learning_style: LearningStyle = LearningStyle.MIXED
    current_emotional_state: EmotionalState = EmotionalState.NEUTRAL
    completed_modules: List[str] = None
    current_module: Optional[str] = None
    confusion_count: int = 0
    confidence_level: float = 0.5  # 0.0 to 1.0
    preferred_pace: str = "medium"  # slow, medium, fast
    interests: List[str] = None
    last_session: Optional[str] = None
    
    def __post_init__(self):
        if self.completed_modules is None:
            self.completed_modules = []
        if self.interests is None:
            self.interests = []


class EmotionDetector:
    """Analyze text and voice patterns to detect emotional state"""
    
    # Keywords that indicate different emotional states
    CONFUSION_KEYWORDS = [
        "confused", "don't understand", "what", "how", "unclear", 
        "lost", "complicated", "difficult", "hard to follow"
    ]
    
    FRUSTRATION_KEYWORDS = [
        "frustrated", "annoyed", "stuck", "not working", "failed",
        "error", "broken", "stupid", "hate", "terrible"
    ]
    
    EXCITEMENT_KEYWORDS = [
        "awesome", "cool", "amazing", "love", "excited", "great",
        "fantastic", "wonderful", "brilliant", "perfect"
    ]
    
    CURIOSITY_KEYWORDS = [
        "tell me more", "what about", "how about", "curious",
        "interested", "want to know", "explore", "dive deeper"
    ]
    
    def analyze_text_emotion(self, text: str) -> EmotionalState:
        """Analyze text for emotional indicators"""
        text_lower = text.lower()
        
        # Count emotional indicators
        confusion_score = sum(1 for word in self.CONFUSION_KEYWORDS if word in text_lower)
        frustration_score = sum(1 for word in self.FRUSTRATION_KEYWORDS if word in text_lower)
        excitement_score = sum(1 for word in self.EXCITEMENT_KEYWORDS if word in text_lower)
        curiosity_score = sum(1 for word in self.CURIOSITY_KEYWORDS if word in text_lower)
        
        # Determine dominant emotion
        scores = {
            EmotionalState.CONFUSED: confusion_score,
            EmotionalState.FRUSTRATED: frustration_score,
            EmotionalState.EXCITED: excitement_score,
            EmotionalState.CURIOUS: curiosity_score
        }
        
        max_emotion = max(scores, key=scores.get)
        if scores[max_emotion] > 0:
            return max_emotion
        
        return EmotionalState.NEUTRAL
    
    def analyze_voice_emotion(self, audio_features: Dict[str, Any]) -> EmotionalState:
        """Analyze voice patterns for emotion (placeholder for future enhancement)"""
        # This would integrate with Hume AI or similar voice emotion detection
        # For now, return neutral
        return EmotionalState.NEUTRAL
    
    def get_teaching_adjustment(self, emotion: EmotionalState) -> Dict[str, Any]:
        """Get teaching adjustments based on detected emotion"""
        adjustments = {
            EmotionalState.CONFUSED: {
                "pace": "slow",
                "explanation_style": "step-by-step with examples",
                "tone": "patient and encouraging",
                "repeat_key_concepts": True,
                "add_analogies": True
            },
            EmotionalState.FRUSTRATED: {
                "pace": "slower",
                "explanation_style": "simplified with reassurance",
                "tone": "calm and supportive",
                "acknowledge_difficulty": True,
                "offer_break": True
            },
            EmotionalState.EXCITED: {
                "pace": "maintain or increase",
                "explanation_style": "detailed with advanced concepts",
                "tone": "enthusiastic and engaging",
                "add_challenges": True,
                "explore_deeper": True
            },
            EmotionalState.CURIOUS: {
                "pace": "medium",
                "explanation_style": "exploratory with multiple examples",
                "tone": "encouraging discovery",
                "ask_questions": True,
                "provide_resources": True
            },
            EmotionalState.NEUTRAL: {
                "pace": "medium",
                "explanation_style": "balanced",
                "tone": "professional and friendly",
                "standard_approach": True
            }
        }
        
        return adjustments.get(emotion, adjustments[EmotionalState.NEUTRAL])


class CurriculumManager:
    """Manage learning modules and progression"""
    
    def __init__(self):
        self.modules = self._load_curriculum()
    
    def _load_curriculum(self) -> Dict[str, Any]:
        """Load curriculum structure"""
        return {
            "ai_fundamentals": {
                "title": "AI Fundamentals → Build Your First AI App",
                "description": "Learn core AI concepts while building a practical application",
                "prerequisites": [],
                "theory_topics": [
                    "What is Artificial Intelligence?",
                    "Machine Learning vs Deep Learning vs AI",
                    "Neural Networks Basics",
                    "Training and Inference"
                ],
                "hands_on_projects": [
                    "Set up Python AI development environment",
                    "Build a simple chatbot with OpenAI API",
                    "Create a text classifier",
                    "Deploy your first AI app"
                ],
                "difficulty": "beginner",
                "estimated_time": "2-3 hours"
            },
            "prompt_engineering": {
                "title": "Prompt Engineering → Create Production Prompts",
                "description": "Master the art of prompt design for reliable AI applications",
                "prerequisites": ["ai_fundamentals"],
                "theory_topics": [
                    "Prompt Engineering Principles",
                    "Few-shot vs Zero-shot Learning",
                    "Chain of Thought Reasoning",
                    "Prompt Security and Safety"
                ],
                "hands_on_projects": [
                    "Design effective prompts for different tasks",
                    "Build a prompt testing framework",
                    "Create prompt templates for production",
                    "Implement prompt validation and safety checks"
                ],
                "difficulty": "intermediate",
                "estimated_time": "3-4 hours"
            },
            "langchain_concepts": {
                "title": "LangChain Architecture → Build RAG Applications",
                "description": "Learn LangChain concepts by building Retrieval Augmented Generation systems",
                "prerequisites": ["ai_fundamentals", "prompt_engineering"],
                "theory_topics": [
                    "LangChain Components Overview",
                    "Document Loaders and Text Splitters",
                    "Vector Stores and Embeddings",
                    "Retrieval Strategies and Chain Types"
                ],
                "hands_on_projects": [
                    "Set up LangChain development environment",
                    "Build a document Q&A system",
                    "Implement semantic search",
                    "Create a production RAG pipeline"
                ],
                "difficulty": "intermediate",
                "estimated_time": "4-5 hours"
            },
            "vector_databases": {
                "title": "Vector Databases → Implement Semantic Search",
                "description": "Understand vector databases through building search systems",
                "prerequisites": ["langchain_concepts"],
                "theory_topics": [
                    "Vector Embeddings and Similarity",
                    "Vector Database Architecture",
                    "Indexing Strategies (HNSW, IVF)",
                    "Performance Optimization"
                ],
                "hands_on_projects": [
                    "Set up Pinecone or Weaviate",
                    "Build semantic search for documents",
                    "Implement hybrid search (semantic + keyword)",
                    "Optimize search performance"
                ],
                "difficulty": "advanced",
                "estimated_time": "4-6 hours"
            },
            "agent_architecture": {
                "title": "AI Agents → Deploy Multi-Agent Systems",
                "description": "Build intelligent agents that can reason and take actions",
                "prerequisites": ["langchain_concepts", "vector_databases"],
                "theory_topics": [
                    "Agent Types and Architectures",
                    "Tool Usage and Function Calling",
                    "Multi-Agent Communication",
                    "Agent Orchestration Patterns"
                ],
                "hands_on_projects": [
                    "Build a research agent with tools",
                    "Create a multi-agent customer service system",
                    "Implement agent memory and persistence",
                    "Deploy agents to production"
                ],
                "difficulty": "advanced",
                "estimated_time": "6-8 hours"
            }
        }
    
    def get_next_module(self, profile: LearnerProfile) -> Optional[str]:
        """Suggest next module based on learner's progress"""
        for module_id, module in self.modules.items():
            if module_id not in profile.completed_modules:
                # Check prerequisites
                prerequisites = module.get("prerequisites", [])
                if all(prereq in profile.completed_modules for prereq in prerequisites):
                    return module_id
        return None
    
    def get_module_content(self, module_id: str, step: int = 0) -> Optional[Dict[str, Any]]:
        """Get specific content for a module step"""
        if module_id not in self.modules:
            return None
        
        module = self.modules[module_id]
        theory_topics = module.get("theory_topics", [])
        hands_on_projects = module.get("hands_on_projects", [])
        
        total_steps = len(theory_topics) + len(hands_on_projects)
        if step >= total_steps:
            return None
        
        if step < len(theory_topics):
            return {
                "type": "theory",
                "content": theory_topics[step],
                "step": step,
                "total_steps": total_steps,
                "module": module
            }
        else:
            project_step = step - len(theory_topics)
            return {
                "type": "hands_on",
                "content": hands_on_projects[project_step],
                "step": step,
                "total_steps": total_steps,
                "module": module
            }


class LearnerProfileManager:
    """Manage learner profiles and persistence"""
    
    def __init__(self, profiles_dir: str = "learner_profiles"):
        self.profiles_dir = Path(profiles_dir)
        self.profiles_dir.mkdir(exist_ok=True)
    
    def save_profile(self, profile: LearnerProfile):
        """Save learner profile to disk"""
        profile_path = self.profiles_dir / f"{profile.user_id}.json"
        profile.last_session = datetime.now().isoformat()
        
        with open(profile_path, 'w') as f:
            json.dump(asdict(profile), f, indent=2)
    
    def load_profile(self, user_id: str) -> LearnerProfile:
        """Load learner profile from disk"""
        profile_path = self.profiles_dir / f"{user_id}.json"
        
        if profile_path.exists():
            with open(profile_path, 'r') as f:
                data = json.load(f)
                # Convert string enums back to enum objects
                if 'learning_style' in data:
                    data['learning_style'] = LearningStyle(data['learning_style'])
                if 'current_emotional_state' in data:
                    data['current_emotional_state'] = EmotionalState(data['current_emotional_state'])
                return LearnerProfile(**data)
        else:
            # Create new profile
            return LearnerProfile(user_id=user_id)
    
    def update_emotional_state(self, user_id: str, emotion: EmotionalState):
        """Update learner's emotional state"""
        profile = self.load_profile(user_id)
        profile.current_emotional_state = emotion
        
        # Track confusion patterns
        if emotion == EmotionalState.CONFUSED:
            profile.confusion_count += 1
            profile.confidence_level = max(0.0, profile.confidence_level - 0.1)
        elif emotion == EmotionalState.EXCITED:
            profile.confidence_level = min(1.0, profile.confidence_level + 0.1)
        
        self.save_profile(profile)
    
    def complete_module(self, user_id: str, module_id: str):
        """Mark module as completed"""
        profile = self.load_profile(user_id)
        if module_id not in profile.completed_modules:
            profile.completed_modules.append(module_id)
        profile.current_module = None
        profile.confidence_level = min(1.0, profile.confidence_level + 0.2)
        self.save_profile(profile)
