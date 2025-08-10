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
        
        # Generate quiz using LLM with higher token limit for complete quiz
        quiz_response = self.llm.generate_quiz(
            user_text=quiz_prompt,
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
Generate a detailed quiz for the chapter: "{title}"

CHAPTER CONTENT:
{content[:3000]}

QUIZ REQUIREMENTS:
- Generate exactly 7-10 multiple choice questions about the specific content above
- Each question must test knowledge of concrete facts, procedures, or concepts from the chapter
- Include 4 options each (A, B, C, D)
- {weak_areas_text}
- Mix difficulty levels: 30% easy, 50% medium, 20% hard
- NO generic reflective questions like "What did you learn?"
- Focus on SPECIFIC content: definitions, examples, steps, formulas, key points

QUESTION TYPES TO INCLUDE:
1. Definition questions: "What is [specific term mentioned]?"
2. Example questions: "Which example was used to demonstrate [concept]?"  
3. Process questions: "What are the steps to [specific process mentioned]?"
4. Comparison questions: "What is the difference between [A] and [B]?"
5. Application questions: "When would you use [specific technique]?"

JSON FORMAT - USE EXACTLY THIS STRUCTURE:
{{
  "questions": [
    {{
      "id": "q1", 
      "question": "Specific question about chapter content?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": 0,
      "explanation": "Clear explanation referencing the chapter content",
      "difficulty": "easy",
      "topic": "specific_topic_name",
      "concepts": ["concept1", "concept2"]
    }}
  ]
}}

CRITICAL: 
- Base ALL questions on the actual chapter content provided above
- Make questions specific and testable
- Avoid vague or subjective questions
- Include 7-10 questions minimum
- Ensure JSON is properly formatted

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
        print(f"Full LLM response length: {len(response)}")
        print(f"Full LLM response: {response}")
        print("=" * 50)
        
        try:
            # Extract JSON from response with better bracket matching
            json_start = response.find('{')
            if json_start == -1:
                print("No JSON found in response")
                return self._generate_fallback_quiz()
            
            # Find the matching closing brace by counting brackets
            bracket_count = 0
            json_end = -1
            for i in range(json_start, len(response)):
                if response[i] == '{':
                    bracket_count += 1
                elif response[i] == '}':
                    bracket_count -= 1
                    if bracket_count == 0:
                        json_end = i + 1
                        break
            
            if json_end == -1:
                print("No matching closing brace found, trying to complete JSON")
                # Try to find incomplete JSON and complete it
                json_str = response[json_start:]
                
                # Check for unterminated strings and complete them
                in_string = False
                escape_next = False
                completed_json = ""
                
                for i, char in enumerate(json_str):
                    if escape_next:
                        completed_json += char
                        escape_next = False
                        continue
                    
                    if char == '\\':
                        escape_next = True
                        completed_json += char
                        continue
                    
                    if char == '"':
                        in_string = not in_string
                        completed_json += char
                    else:
                        completed_json += char
                
                # If we're still in a string at the end, close it
                if in_string:
                    completed_json += '"'
                
                # Add missing closing brackets
                open_braces = completed_json.count('{') - completed_json.count('}')
                open_brackets = completed_json.count('[') - completed_json.count(']')
                
                # If we're in the middle of a question object, try to close it properly
                if '{"id":' in completed_json[-100:] and completed_json.strip().endswith('"'):
                    # We're likely in an incomplete question, remove the incomplete part
                    # Find the last complete question
                    last_complete = completed_json.rfind('    },')
                    if last_complete != -1:
                        completed_json = completed_json[:last_complete + 6]  # Keep the },
                
                json_str = completed_json + ']' * open_brackets + '}' * open_braces
            else:
                json_str = response[json_start:json_end]
            
            # Clean up common JSON issues
            import re
            # Remove HTML tags first (like <sup>, <sub>, etc.)
            json_str = re.sub(r'<[^>]+>', '', json_str)
            
            # Handle mathematical symbols and special characters that break JSON
            json_str = json_str.replace('≥', '>=')  # Replace unicode greater-than-or-equal
            json_str = json_str.replace('≤', '<=')  # Replace unicode less-than-or-equal
            json_str = json_str.replace('∞', 'infinity')  # Replace infinity symbol
            json_str = json_str.replace('∈', 'in')  # Replace element-of symbol
            json_str = json_str.replace('∀', 'for all')  # Replace for-all symbol
            json_str = json_str.replace('∃', 'there exists')  # Replace exists symbol
            
            # Replace angle brackets that might be interpreted as HTML
            json_str = re.sub(r'<([^>]*?)>', r'(\\1)', json_str)  # Replace <x,y> with (x,y)
            
            # Fix common JSON syntax issues
            json_str = re.sub(r',\s*}', '}', json_str)  # Remove trailing commas before }
            json_str = re.sub(r',\s*]', ']', json_str)  # Remove trailing commas before ]
            
            # Handle unescaped quotes - simple approach
            # Replace smart quotes with regular quotes first
            json_str = json_str.replace('"', '"').replace('"', '"')
            json_str = json_str.replace(''', "'").replace(''', "'")
            
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
