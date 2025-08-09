"""
ProfAI Specialization System
Defines different learning paths and delivery formats
"""
from __future__ import annotations
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass


class LearningPath(Enum):
    THEORY = "theory"
    TOOLING = "tooling" 
    HYBRID = "hybrid"


class DeliveryFormat(Enum):
    MICRO_LEARNING = "micro_learning"  # Short daily lessons
    DEEP_DIVE = "deep_dive"           # Step-by-step tutorials
    SLIDE_BASED = "slide_based"       # Module-based learning
    AUDIO_LESSONS = "audio_lessons"   # Podcast style
    VIDEO_TUTORIALS = "video_tutorials" # YouTube-style


@dataclass
class LessonPlan:
    title: str
    path: LearningPath
    format: DeliveryFormat
    duration_minutes: int
    difficulty: str  # beginner, intermediate, advanced
    prerequisites: List[str]
    learning_objectives: List[str]
    content_outline: List[str]


# Theory-focused curriculum
THEORY_LESSONS = {
    "ai_fundamentals": LessonPlan(
        title="AI Fundamentals: From Narrow to General Intelligence",
        path=LearningPath.THEORY,
        format=DeliveryFormat.MICRO_LEARNING,
        duration_minutes=10,
        difficulty="beginner",
        prerequisites=[],
        learning_objectives=[
            "Distinguish between narrow and general AI",
            "Understand key AI paradigms",
            "Identify real-world AI applications"
        ],
        content_outline=[
            "What is AI? Definition and scope",
            "Types of AI: Narrow vs General vs Super",
            "Current AI capabilities and limitations",
            "Real-world examples and applications"
        ]
    ),
    
    "machine_learning_basics": LessonPlan(
        title="Machine Learning Core Concepts",
        path=LearningPath.THEORY,
        format=DeliveryFormat.DEEP_DIVE,
        duration_minutes=25,
        difficulty="beginner",
        prerequisites=["ai_fundamentals"],
        learning_objectives=[
            "Understand supervised vs unsupervised learning",
            "Grasp the concept of training data",
            "Identify when to use different ML approaches"
        ],
        content_outline=[
            "Supervised learning: classification and regression",
            "Unsupervised learning: clustering and dimensionality reduction",
            "Reinforcement learning basics",
            "Training, validation, and test sets",
            "Overfitting and generalization"
        ]
    ),
    
    "prompt_engineering": LessonPlan(
        title="Prompt Engineering Mastery",
        path=LearningPath.THEORY,
        format=DeliveryFormat.DEEP_DIVE,
        duration_minutes=20,
        difficulty="intermediate",
        prerequisites=["ai_fundamentals"],
        learning_objectives=[
            "Master prompt engineering techniques",
            "Design effective prompts for different tasks",
            "Understand prompt optimization strategies"
        ],
        content_outline=[
            "Prompt engineering fundamentals",
            "Chain-of-thought prompting",
            "Few-shot vs zero-shot learning",
            "Prompt templates and best practices",
            "Common pitfalls and how to avoid them"
        ]
    )
}

# Tooling-focused curriculum  
TOOLING_LESSONS = {
    "langchain_basics": LessonPlan(
        title="Building with LangChain: Your First Agent",
        path=LearningPath.TOOLING,
        format=DeliveryFormat.VIDEO_TUTORIALS,
        duration_minutes=30,
        difficulty="beginner",
        prerequisites=[],
        learning_objectives=[
            "Set up LangChain development environment",
            "Build a simple AI agent",
            "Integrate with external APIs"
        ],
        content_outline=[
            "LangChain installation and setup",
            "Creating your first chain",
            "Adding memory to conversations",
            "Integrating tools and APIs",
            "Testing and debugging agents"
        ]
    ),
    
    "huggingface_deployment": LessonPlan(
        title="Deploying Models with Hugging Face",
        path=LearningPath.TOOLING,
        format=DeliveryFormat.DEEP_DIVE,
        duration_minutes=35,
        difficulty="intermediate",
        prerequisites=["langchain_basics"],
        learning_objectives=[
            "Deploy models to Hugging Face Hub",
            "Create interactive demos with Gradio",
            "Set up model inference endpoints"
        ],
        content_outline=[
            "Hugging Face ecosystem overview",
            "Model uploading and versioning",
            "Creating Gradio interfaces",
            "Setting up inference endpoints",
            "Monitoring and scaling deployments"
        ]
    ),
    
    "ai_agent_architecture": LessonPlan(
        title="AI Agent Architecture Patterns",
        path=LearningPath.TOOLING,
        format=DeliveryFormat.DEEP_DIVE,
        duration_minutes=40,
        difficulty="advanced",
        prerequisites=["langchain_basics", "huggingface_deployment"],
        learning_objectives=[
            "Design scalable AI agent architectures",
            "Implement agent communication patterns",
            "Build multi-agent systems"
        ],
        content_outline=[
            "Agent design patterns",
            "Tool integration strategies",
            "Multi-agent coordination",
            "State management and persistence",
            "Performance optimization techniques"
        ]
    )
}

# Hybrid lessons that combine theory and practice
HYBRID_LESSONS = {
    "neural_networks_implementation": LessonPlan(
        title="Neural Networks: Theory to Code",
        path=LearningPath.HYBRID,
        format=DeliveryFormat.DEEP_DIVE,
        duration_minutes=45,
        difficulty="intermediate",
        prerequisites=["machine_learning_basics"],
        learning_objectives=[
            "Understand neural network mathematics",
            "Implement a neural network from scratch",
            "Use PyTorch for practical applications"
        ],
        content_outline=[
            "Mathematical foundations of neural networks",
            "Forward and backward propagation",
            "Implementing perceptron from scratch",
            "Building networks with PyTorch",
            "Training on real datasets"
        ]
    )
}

ALL_LESSONS = {**THEORY_LESSONS, **TOOLING_LESSONS, **HYBRID_LESSONS}


def get_lesson_by_id(lesson_id: str) -> Optional[LessonPlan]:
    """Get a specific lesson by its ID"""
    return ALL_LESSONS.get(lesson_id)


def get_lessons_by_path(path: LearningPath) -> Dict[str, LessonPlan]:
    """Get all lessons for a specific learning path"""
    return {
        lesson_id: lesson 
        for lesson_id, lesson in ALL_LESSONS.items() 
        if lesson.path == path
    }


def get_lessons_by_format(format: DeliveryFormat) -> Dict[str, LessonPlan]:
    """Get all lessons for a specific delivery format"""
    return {
        lesson_id: lesson 
        for lesson_id, lesson in ALL_LESSONS.items() 
        if lesson.format == format
    }


def recommend_next_lesson(completed_lessons: List[str], preferred_path: LearningPath) -> Optional[str]:
    """Recommend the next lesson based on completed lessons and learning path"""
    available_lessons = get_lessons_by_path(preferred_path)
    
    for lesson_id, lesson in available_lessons.items():
        if lesson_id not in completed_lessons:
            # Check if prerequisites are met
            if all(prereq in completed_lessons for prereq in lesson.prerequisites):
                return lesson_id
    
    return None
