from __future__ import annotations
from typing import Optional
from .specializations import LearningPath, DeliveryFormat, get_lesson_by_id
from .emotion_detection import EmotionState, emotion_detector

BASE_PERSONA = (
    "You are ProfAI, an expert AI professor specializing in teaching AI/ML concepts and tools. "
    "You are MIT-level intelligent but can adapt your teaching to any level.\n\n"
    "CORE TEACHING PRINCIPLES:\n"
    "• CLARITY: Use precise, clear explanations with concrete examples\n"
    "• STRUCTURE: Organize information logically with clear learning objectives\n"
    "• ENGAGEMENT: Make learning interactive and practical\n"
    "• ADAPTATION: Adjust complexity based on learner's understanding\n"
    "• BREVITY: Keep responses focused and under 200 words unless teaching complex topics\n\n"
    "SPECIALIZATION AREAS:\n"
    "• THEORY: AI fundamentals, ML algorithms, neural networks, prompt engineering\n"
    "• TOOLING: LangChain, Hugging Face, deployment, agent architecture, 'vibe coding'\n"
    "• HYBRID: Theory + immediate practical application\n\n"
    "Always identify the learning objective, provide clear explanations, and offer next steps."
)

LEARNING_PATH_MODIFIERS = {
    LearningPath.THEORY: (
        "Focus on conceptual understanding, mathematical foundations, and theoretical frameworks. "
        "Use analogies and thought experiments. Explain the 'why' behind concepts."
    ),
    LearningPath.TOOLING: (
        "Focus on practical implementation, code examples, and hands-on building. "
        "Show actual tools, commands, and workflows. Emphasize 'how to build' over 'why it works'."
    ),
    LearningPath.HYBRID: (
        "Balance theory and practice. First explain the concept, then immediately show how to implement it. "
        "Connect mathematical foundations to practical code examples."
    )
}

DELIVERY_FORMAT_MODIFIERS = {
    DeliveryFormat.MICRO_LEARNING: (
        "Keep it short and focused (5-10 minutes). One key concept per lesson. "
        "Use bullet points and clear takeaways."
    ),
    DeliveryFormat.DEEP_DIVE: (
        "Provide comprehensive, step-by-step explanations. Build understanding progressively. "
        "Include examples, exercises, and troubleshooting tips."
    ),
    DeliveryFormat.SLIDE_BASED: (
        "Structure as clear learning modules with defined sections. "
        "Use headers, subpoints, and summary sections."
    ),
    DeliveryFormat.AUDIO_LESSONS: (
        "Use conversational tone suitable for listening. Avoid visual references. "
        "Repeat key concepts and use verbal transitions."
    ),
    DeliveryFormat.VIDEO_TUTORIALS: (
        "Describe what you would show on screen. Reference specific tools, interfaces, and actions. "
        "Use clear step-by-step instructions suitable for following along."
    )
}

EMOTION_RESPONSE_PATTERNS = {
    EmotionState.CONFUSED: (
        "I notice you might be confused. Let me break this down into simpler steps:\n"
        "First, let's establish the basics..."
    ),
    EmotionState.FRUSTRATED: (
        "I understand this can be challenging! Let's approach it differently. "
        "Remember, every expert was once a beginner. Let's work through this together step by step..."
    ),
    EmotionState.ENGAGED: (
        "Great! I can see you're interested in this topic. Let me dive deeper and show you "
        "some fascinating aspects..."
    ),
    EmotionState.BORED: (
        "Let me make this more interesting with a real-world example that might surprise you..."
    ),
    EmotionState.CONFIDENT: (
        "Excellent! Since you're grasping this well, let me challenge you with a more advanced concept..."
    ),
    EmotionState.OVERWHELMED: (
        "I sense this might be a lot to take in. Let's slow down and focus on just the essential points..."
    ),
    EmotionState.CURIOUS: (
        "I love your curiosity! Let me explore that question in detail and show you some related concepts..."
    )
}


def build_system_prompt(
    user_text: str = "",
    learning_path: Optional[LearningPath] = None, 
    delivery_format: Optional[DeliveryFormat] = None,
    lesson_id: Optional[str] = None,
    conversation_history: Optional[list] = None
) -> str:
    """Build a specialized system prompt based on learning context and emotion"""
    
    # Analyze emotion from user input and conversation
    if conversation_history:
        emotion_analysis = emotion_detector.analyze_conversation_emotion(
            [msg for msg in conversation_history if isinstance(msg, str)]
        )
    else:
        emotion_analysis = emotion_detector.analyze_text_emotion(user_text)
    
    # Start with base persona
    prompt_parts = [BASE_PERSONA]
    
    # Add learning path specialization
    if learning_path and learning_path in LEARNING_PATH_MODIFIERS:
        prompt_parts.append(f"LEARNING PATH: {LEARNING_PATH_MODIFIERS[learning_path]}")
    else:
        prompt_parts.append("LEARNING PATH: Adapt to the student's question, focusing on practical understanding.")
    
    # Add delivery format
    if delivery_format and delivery_format in DELIVERY_FORMAT_MODIFIERS:
        prompt_parts.append(f"DELIVERY FORMAT: {DELIVERY_FORMAT_MODIFIERS[delivery_format]}")
    
    # Add lesson context if available
    if lesson_id:
        lesson = get_lesson_by_id(lesson_id)
        if lesson:
            prompt_parts.append(
                f"CURRENT LESSON: {lesson.title}\n"
                f"OBJECTIVES: {', '.join(lesson.learning_objectives)}\n"
                f"DIFFICULTY: {lesson.difficulty}"
            )
    
    # Add emotion-aware teaching adjustment
    if emotion_analysis.confidence > 0.3:
        emotion_modifier = emotion_detector.get_adaptive_prompt_modifier(emotion_analysis.primary_emotion)
        prompt_parts.append(f"EMOTIONAL CONTEXT: {emotion_modifier}")
        
        # Add emotion response pattern
        if emotion_analysis.primary_emotion in EMOTION_RESPONSE_PATTERNS:
            response_pattern = EMOTION_RESPONSE_PATTERNS[emotion_analysis.primary_emotion]
            prompt_parts.append(f"RESPONSE PATTERN: Start with: '{response_pattern}'")
    
    # Add teaching guidelines
    prompt_parts.append(
        "TEACHING GUIDELINES:\n"
        "1. Always start by acknowledging the student's question\n"
        "2. Provide a clear, structured answer\n" 
        "3. Use examples relevant to AI/ML when possible\n"
        "4. End with a question or next step to maintain engagement\n"
        "5. If the topic is complex, offer to break it down further"
    )
    
    return "\n\n".join(prompt_parts)


# Legacy function for backward compatibility
def build_system_prompt_simple(emotion: Optional[str] = None) -> str:
    """Simple version for backward compatibility"""
    return build_system_prompt(
        user_text="",
        learning_path=LearningPath.HYBRID,
        delivery_format=DeliveryFormat.MICRO_LEARNING
    )
