"""
Personalized Quiz Generation System
Generates adaptive quizzes based on chapter completion and learning patterns
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json
import random
from .llm import LLMClient

@dataclass
class QuizQuestion:
    id: str
    question: str
    options: List[str]
    correct_answer: int  # index of correct option
    explanation: str
    difficulty: str  # easy, medium, hard
    topic: str
    concepts: List[str]

@dataclass
class QuizResult:
    score: float
    total_questions: int
    correct_answers: int
    weak_concepts: List[str]
    strong_concepts: List[str]
    recommendations: List[str]

class PersonalizedQuizGenerator:
    def __init__(self):
        self.llm = LLMClient()
    
    def generate_chapter_quiz(
        self, 
        chapter_content: str, 
        chapter_title: str,
        user_learning_history: Optional[Dict] = None,
        difficulty_preference: str = "mixed"
    ) -> List[QuizQuestion]:
        """Generate a personalized quiz based on chapter content and user history"""
        
        # Analyze user's weak areas from history
        weak_areas = self._extract_weak_areas(user_learning_history) if user_learning_history else []
        
        # Generate quiz prompt
        quiz_prompt = self._build_quiz_prompt(
            chapter_content, 
            chapter_title, 
            weak_areas, 
            difficulty_preference
        )
        
        # Generate quiz using LLM
        quiz_response = self.llm.generate(
            user_text=quiz_prompt,
            learning_path=None,
            temperature=0.7
        )
        
        # Parse and structure the quiz
        questions = self._parse_quiz_response(quiz_response)
        
        return questions
    
    def _build_quiz_prompt(
        self, 
        content: str, 
        title: str, 
        weak_areas: List[str], 
        difficulty: str
    ) -> str:
        """Build comprehensive quiz generation prompt"""
        
        weak_areas_text = f"Focus extra attention on these areas where the user struggles: {', '.join(weak_areas)}" if weak_areas else ""
        
        return f"""
Generate a personalized adaptive quiz for the chapter: "{title}"

CHAPTER CONTENT:
{content[:2000]}...

QUIZ REQUIREMENTS:
- Generate 5-8 questions of varying difficulty
- Include multiple choice questions (4 options each)
- {weak_areas_text}
- Mix difficulty levels: {difficulty}
- Focus on practical application and conceptual understanding
- Include detailed explanations for each answer

RESPONSE FORMAT (JSON):
{{
  "questions": [
    {{
      "id": "q1",
      "question": "Clear, specific question text",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": 0,
      "explanation": "Detailed explanation of why this is correct",
      "difficulty": "easy|medium|hard",
      "topic": "specific topic name",
      "concepts": ["concept1", "concept2"]
    }}
  ]
}}

Generate the quiz now:
"""
    
    def _extract_weak_areas(self, learning_history: Dict) -> List[str]:
        """Extract areas where user has struggled based on history"""
        weak_areas = []
        
        if 'quiz_results' in learning_history:
            for result in learning_history['quiz_results']:
                if result.get('score', 1.0) < 0.7:  # Less than 70%
                    weak_areas.extend(result.get('weak_concepts', []))
        
        if 'confusion_topics' in learning_history:
            weak_areas.extend(learning_history['confusion_topics'])
        
        # Remove duplicates and return top weak areas
        return list(set(weak_areas))[:5]
    
    def _parse_quiz_response(self, response: str) -> List[QuizQuestion]:
        """Parse LLM response into structured quiz questions with robust error handling"""
        try:
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start == -1 or json_end == 0:
                print("No JSON found in response")
                return self._generate_fallback_quiz()
                
            json_str = response[json_start:json_end]
            
            # Clean up common JSON issues
            import re
            json_str = re.sub(r',\s*}', '}', json_str)  # Remove trailing commas before }
            json_str = re.sub(r',\s*]', ']', json_str)  # Remove trailing commas before ]
            json_str = json_str.replace("'", '"')  # Replace single quotes with double quotes
            
            print(f"Attempting to parse JSON: {json_str[:200]}...")
            quiz_data = json.loads(json_str)
            questions = []
            
            for i, q_data in enumerate(quiz_data.get('questions', [])):
                try:
                    # Validate required fields
                    if not q_data.get('question') or not q_data.get('options'):
                        print(f"Skipping invalid question {i}: missing question or options")
                        continue
                        
                    if len(q_data.get('options', [])) < 2:
                        print(f"Skipping question {i}: not enough options")
                        continue
                    
                    question = QuizQuestion(
                        id=q_data.get('id', f'q{i+1}'),
                        question=q_data.get('question', '').strip(),
                        options=q_data.get('options', []),
                        correct_answer=int(q_data.get('correct_answer', 0)),
                        explanation=q_data.get('explanation', '').strip(),
                        difficulty=q_data.get('difficulty', 'medium'),
                        topic=q_data.get('topic', 'general'),
                        concepts=q_data.get('concepts', ['general'])
                    )
                    questions.append(question)
                    print(f"Successfully parsed question {i+1}: {question.question[:50]}...")
                except Exception as e:
                    print(f"Error parsing individual question {i}: {e}")
                    continue
            
            if len(questions) > 0:
                print(f"Successfully parsed {len(questions)} questions")
                return questions
            else:
                print("No valid questions found, using fallback")
                return self._generate_better_fallback_quiz()
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Problematic JSON: {json_str if 'json_str' in locals() else response[:500]}")
            return self._generate_better_fallback_quiz()
        except Exception as e:
            print(f"Error parsing quiz response: {e}")
            return self._generate_better_fallback_quiz()
    
    def _generate_fallback_quiz(self) -> List[QuizQuestion]:
        """Generate basic fallback quiz if parsing fails"""
        return [
            QuizQuestion(
                id="fallback1",
                question="What did you learn from this chapter?",
                options=[
                    "New concepts and applications",
                    "Nothing new",
                    "Some useful information",
                    "Everything was confusing"
                ],
                correct_answer=0,
                explanation="Learning new concepts is the goal of each chapter.",
                difficulty="easy",
                topic="general",
                concepts=["learning", "comprehension"]
            )
        ]
    
    def _generate_better_fallback_quiz(self) -> List[QuizQuestion]:
        """Generate a more comprehensive fallback quiz"""
        return [
            QuizQuestion(
                id="fallback1",
                question="What was the main topic covered in this chapter?",
                options=[
                    "The core concepts and their applications",
                    "Random unrelated information",
                    "Only basic definitions",
                    "Abstract theories without examples"
                ],
                correct_answer=0,
                explanation="Chapters typically focus on core concepts and their practical applications.",
                difficulty="easy",
                topic="comprehension",
                concepts=["understanding", "main ideas"]
            ),
            QuizQuestion(
                id="fallback2",
                question="How would you apply what you learned?",
                options=[
                    "Practice with real-world examples",
                    "Memorize all definitions",
                    "Skip to the next chapter",
                    "Only read the summary"
                ],
                correct_answer=0,
                explanation="Active practice with real-world examples helps solidify learning.",
                difficulty="medium",
                topic="application",
                concepts=["practical application", "skill development"]
            ),
            QuizQuestion(
                id="fallback3",
                question="What should be your next learning step?",
                options=[
                    "Review and practice the concepts",
                    "Move on without understanding",
                    "Only read more theory",
                    "Ask someone else to explain everything"
                ],
                correct_answer=0,
                explanation="Reviewing and practicing helps reinforce understanding before moving forward.",
                difficulty="easy",
                topic="learning strategy",
                concepts=["review", "practice", "learning progression"]
            )
        ]
    
    def evaluate_quiz_results(
        self, 
        questions: List[QuizQuestion], 
        user_answers: List[int]
    ) -> QuizResult:
        """Evaluate quiz performance and generate recommendations"""
        
        correct_count = 0
        weak_concepts = []
        strong_concepts = []
        
        for i, (question, answer) in enumerate(zip(questions, user_answers)):
            if answer == question.correct_answer:
                correct_count += 1
                strong_concepts.extend(question.concepts)
            else:
                weak_concepts.extend(question.concepts)
        
        score = correct_count / len(questions) if questions else 0
        
        # Generate recommendations
        recommendations = self._generate_recommendations(score, weak_concepts, strong_concepts)
        
        return QuizResult(
            score=score,
            total_questions=len(questions),
            correct_answers=correct_count,
            weak_concepts=list(set(weak_concepts)),
            strong_concepts=list(set(strong_concepts)),
            recommendations=recommendations
        )
    
    def _generate_recommendations(
        self, 
        score: float, 
        weak_concepts: List[str], 
        strong_concepts: List[str]
    ) -> List[str]:
        """Generate personalized learning recommendations"""
        
        recommendations = []
        
        if score >= 0.9:
            recommendations.append("🎉 Excellent work! You've mastered this chapter.")
            recommendations.append("🚀 Ready for advanced topics in this area.")
        elif score >= 0.7:
            recommendations.append("👍 Good understanding! Minor review needed.")
            if weak_concepts:
                recommendations.append(f"📝 Review these concepts: {', '.join(weak_concepts[:3])}")
        elif score >= 0.5:
            recommendations.append("📚 Partial understanding. More study recommended.")
            recommendations.append(f"🔍 Focus on: {', '.join(weak_concepts[:3])}")
            recommendations.append("💡 Try different learning approaches for difficult concepts.")
        else:
            recommendations.append("🔄 Chapter review strongly recommended.")
            recommendations.append("👨‍🏫 Consider asking for help with core concepts.")
            recommendations.append("📖 Re-read the chapter and take notes.")
        
        return recommendations
