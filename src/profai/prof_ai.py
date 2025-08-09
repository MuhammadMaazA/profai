from __future__ import annotations
from typing import Optional, Dict, Any, List
import os
from datetime import datetime

from .llm import LLMClient
from .education import (
    EmotionDetector, CurriculumManager, LearnerProfileManager,
    EmotionalState, LearnerProfile, LearningStyle
)


class ProfAIEducationClient:
    """Enhanced AI Professor with emotional intelligence and curriculum management"""
    
    def __init__(self):
        self.llm_client = LLMClient()
        self.emotion_detector = EmotionDetector()
        self.curriculum_manager = CurriculumManager()
        self.profile_manager = LearnerProfileManager()
    
    def generate_educational_response(
        self, 
        user_text: str, 
        user_id: str = "default_user",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate an educational response with emotional intelligence"""
        
        # Load learner profile
        profile = self.profile_manager.load_profile(user_id)
        
        # Detect emotion from text
        detected_emotion = self.emotion_detector.analyze_text_emotion(user_text)
        
        # Update emotional state if significant change detected
        if detected_emotion != EmotionalState.NEUTRAL:
            profile.current_emotional_state = detected_emotion
            self.profile_manager.update_emotional_state(user_id, detected_emotion)
        
        # Get teaching adjustments based on emotion
        teaching_adjustments = self.emotion_detector.get_teaching_adjustment(
            profile.current_emotional_state
        )
        
        # Build educational context
        educational_context = self._build_educational_context(profile, context)
        
        # Generate response with educational intelligence
        response = self._generate_professor_response(
            user_text=user_text,
            profile=profile,
            teaching_adjustments=teaching_adjustments,
            educational_context=educational_context
        )
        
        # Save updated profile
        self.profile_manager.save_profile(profile)
        
        return {
            "response": response,
            "detected_emotion": detected_emotion.value,
            "teaching_adjustments": teaching_adjustments,
            "current_module": profile.current_module,
            "confidence_level": profile.confidence_level,
            "suggested_next_action": self._get_suggested_action(profile)
        }
    
    def _build_educational_context(
        self, 
        profile: LearnerProfile, 
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build comprehensive educational context"""
        
        context = {
            "learner_profile": {
                "completed_modules": profile.completed_modules,
                "current_module": profile.current_module,
                "learning_style": profile.learning_style.value,
                "confidence_level": profile.confidence_level,
                "confusion_count": profile.confusion_count,
                "preferred_pace": profile.preferred_pace
            },
            "available_modules": list(self.curriculum_manager.modules.keys()),
            "session_timestamp": datetime.now().isoformat()
        }
        
        # Add current module content if applicable
        if profile.current_module:
            module_content = self.curriculum_manager.get_module_content(
                profile.current_module, 
                step=0  # For now, get first step
            )
            if module_content:
                context["current_lesson"] = module_content
        
        # Suggest next module if none in progress
        else:
            next_module = self.curriculum_manager.get_next_module(profile)
            if next_module:
                context["suggested_module"] = {
                    "id": next_module,
                    "details": self.curriculum_manager.modules[next_module]
                }
        
        # Merge additional context
        if additional_context:
            context.update(additional_context)
        
        return context
    
    def _generate_professor_response(
        self,
        user_text: str,
        profile: LearnerProfile,
        teaching_adjustments: Dict[str, Any],
        educational_context: Dict[str, Any]
    ) -> str:
        """Generate response using educational intelligence"""
        
        # Build professor system prompt
        system_prompt = self._build_professor_prompt(profile, teaching_adjustments, educational_context)
        
        # Generate response
        response = self.llm_client.generate(
            user_text=user_text,
            emotion=profile.current_emotional_state.value,
            temperature=0.7
        )
        
        # Post-process response based on teaching adjustments
        response = self._apply_teaching_adjustments(response, teaching_adjustments)
        
        return response
    
    def _build_professor_prompt(
        self,
        profile: LearnerProfile,
        teaching_adjustments: Dict[str, Any],
        educational_context: Dict[str, Any]
    ) -> str:
        """Build system prompt for ProfAI professor"""
        
        base_prompt = """You are ProfAI, an MIT-style AI professor with deep expertise in AI/ML theory and practical implementation. You specialize in teaching both concepts and hands-on skills.

Your teaching philosophy:
- Theory + Practice: Always connect concepts to real-world implementation
- Adaptive Learning: Adjust your teaching style based on student's emotional state and progress
- Encouraging Mentor: Support students through challenges while maintaining high standards
- Current & Practical: Use latest tools, frameworks, and industry best practices

"""
        
        # Add emotional intelligence context
        emotion_context = f"""
STUDENT'S CURRENT STATE:
- Emotional State: {profile.current_emotional_state.value}
- Confidence Level: {profile.confidence_level:.1f}/1.0
- Learning Style: {profile.learning_style.value}
- Confusion Count: {profile.confusion_count}

TEACHING ADJUSTMENTS:
- Pace: {teaching_adjustments.get('pace', 'medium')}
- Explanation Style: {teaching_adjustments.get('explanation_style', 'balanced')}
- Tone: {teaching_adjustments.get('tone', 'professional and friendly')}
"""
        
        # Add curriculum context
        curriculum_context = "\nCURRICULUM CONTEXT:\n"
        if profile.completed_modules:
            curriculum_context += f"- Completed: {', '.join(profile.completed_modules)}\n"
        
        if profile.current_module:
            curriculum_context += f"- Current Module: {profile.current_module}\n"
        elif "suggested_module" in educational_context:
            suggested = educational_context["suggested_module"]
            curriculum_context += f"- Suggested Next: {suggested['details']['title']}\n"
        
        # Add specific teaching instructions based on emotional state
        teaching_instructions = self._get_teaching_instructions(profile.current_emotional_state, teaching_adjustments)
        
        return base_prompt + emotion_context + curriculum_context + teaching_instructions
    
    def _get_teaching_instructions(self, emotion: EmotionalState, adjustments: Dict[str, Any]) -> str:
        """Get specific teaching instructions based on emotional state"""
        
        instructions = "\nTEACHING INSTRUCTIONS:\n"
        
        if emotion == EmotionalState.CONFUSED:
            instructions += """
- Break down concepts into smaller, digestible pieces
- Use analogies and real-world examples
- Ask clarifying questions to identify specific confusion points
- Offer step-by-step explanations
- Reassure that confusion is normal and part of learning
"""
        
        elif emotion == EmotionalState.FRUSTRATED:
            instructions += """
- Acknowledge the difficulty and validate their feelings
- Simplify explanations and slow down the pace
- Offer encouragement and remind them of their progress
- Suggest taking a short break if needed
- Focus on building confidence with easier examples first
"""
        
        elif emotion == EmotionalState.EXCITED:
            instructions += """
- Match their energy and enthusiasm
- Provide deeper insights and advanced concepts
- Challenge them with interesting problems
- Encourage exploration of related topics
- Share cutting-edge developments in the field
"""
        
        elif emotion == EmotionalState.CURIOUS:
            instructions += """
- Encourage their curiosity with detailed explanations
- Provide multiple perspectives and approaches
- Ask thought-provoking questions
- Suggest additional resources and learning paths
- Connect concepts to broader implications
"""
        
        else:  # NEUTRAL or default
            instructions += """
- Maintain a balanced, engaging teaching style
- Combine theory with practical examples
- Check for understanding regularly
- Encourage questions and active participation
"""
        
        return instructions
    
    def _apply_teaching_adjustments(self, response: str, adjustments: Dict[str, Any]) -> str:
        """Apply post-processing adjustments to the response"""
        
        # For now, return response as-is
        # Future enhancements could include:
        # - Adding visual indicators for different learning styles
        # - Inserting code examples for kinesthetic learners
        # - Adding audio cues or emphasis
        
        return response
    
    def _get_suggested_action(self, profile: LearnerProfile) -> str:
        """Get suggested next action for the learner"""
        
        if profile.current_module is None:
            next_module = self.curriculum_manager.get_next_module(profile)
            if next_module:
                module_info = self.curriculum_manager.modules[next_module]
                return f"Start learning: {module_info['title']}"
            else:
                return "Explore advanced topics or review completed modules"
        
        return f"Continue with current module: {profile.current_module}"
    
    def start_module(self, user_id: str, module_id: str) -> Dict[str, Any]:
        """Start a new learning module"""
        if module_id not in self.curriculum_manager.modules:
            return {"error": f"Module {module_id} not found"}
        
        profile = self.profile_manager.load_profile(user_id)
        profile.current_module = module_id
        self.profile_manager.save_profile(profile)
        
        module_info = self.curriculum_manager.modules[module_id]
        first_step = self.curriculum_manager.get_module_content(module_id, 0)
        
        return {
            "module_started": module_id,
            "module_info": module_info,
            "first_step": first_step,
            "welcome_message": f"Welcome to {module_info['title']}! Let's start with understanding {first_step['content'] if first_step else 'the basics'}."
        }
    
    def get_learning_progress(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive learning progress"""
        profile = self.profile_manager.load_profile(user_id)
        
        total_modules = len(self.curriculum_manager.modules)
        completed_count = len(profile.completed_modules)
        progress_percentage = (completed_count / total_modules) * 100 if total_modules > 0 else 0
        
        return {
            "user_id": user_id,
            "progress_percentage": round(progress_percentage, 1),
            "completed_modules": profile.completed_modules,
            "current_module": profile.current_module,
            "confidence_level": profile.confidence_level,
            "learning_style": profile.learning_style.value,
            "total_modules_available": total_modules,
            "suggested_next": self._get_suggested_action(profile)
        }
