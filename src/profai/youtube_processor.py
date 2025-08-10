"""
YouTube Video Processing and Flashcard Generation Module
Handles YouTube URL processing, content extraction, and educational flashcard creation.
"""

from __future__ import annotations
import re
import json
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import tempfile
import os

import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

from .llm import LLMClient


@dataclass
class Flashcard:
    """Individual flashcard with question, answer, and metadata"""
    id: str
    question: str
    answer: str
    category: str
    difficulty: str  # easy, medium, hard
    tags: List[str]
    status: str = "new"  # new, learning, learned, review
    review_count: int = 0
    created_at: str = ""
    last_reviewed: str = ""


@dataclass
class FlashcardSet:
    """Collection of flashcards from a video"""
    id: str
    title: str
    description: str
    video_url: str
    video_title: str
    video_duration: str
    cards: List[Flashcard]
    created_at: str
    total_cards: int = 0
    learned_cards: int = 0
    learning_cards: int = 0
    
    def __post_init__(self):
        self.total_cards = len(self.cards)
        self.learned_cards = len([c for c in self.cards if c.status == "learned"])
        self.learning_cards = len([c for c in self.cards if c.status == "learning"])


class YouTubeProcessor:
    """Processes YouTube videos and generates educational flashcards"""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()
        self.data_dir = Path(__file__).resolve().parents[2] / "data" / "flashcards"
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from various URL formats"""
        patterns = [
            r'(?:https?://)?(?:www\.)?youtube\.com/watch\?.*v=([a-zA-Z0-9_-]{11})',
            r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})',
            r'(?:https?://)?youtu\.be/([a-zA-Z0-9_-]{11})',
            r'(?:https?://)?(?:www\.)?youtube\.com/v/([a-zA-Z0-9_-]{11})',
            r'(?:https?://)?(?:m\.)?youtube\.com/watch\?.*v=([a-zA-Z0-9_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def get_video_info(self, url: str) -> Dict[str, Any]:
        """Get video metadata using yt-dlp"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extractaudio': False,
                'skip_download': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                return {
                    "title": info.get("title", "Unknown Title"),
                    "description": info.get("description", ""),
                    "duration": info.get("duration", 0),
                    "uploader": info.get("uploader", "Unknown"),
                    "upload_date": info.get("upload_date", ""),
                    "view_count": info.get("view_count", 0),
                    "categories": info.get("categories", []),
                    "tags": info.get("tags", []),
                    "thumbnail": info.get("thumbnail", ""),
                }
        except Exception as e:
            raise RuntimeError(f"Failed to get video info: {str(e)}")
    
    def get_transcript(self, video_id: str) -> str:
        """Get video transcript using youtube-transcript-api"""
        try:
            # Create API instance
            api = YouTubeTranscriptApi()
            
            # Try to get transcript
            transcript_data = api.fetch(video_id)
            formatter = TextFormatter()
            return formatter.format_transcript(transcript_data)
            
        except Exception as e:
            raise RuntimeError(f"Failed to get transcript: {str(e)}")
    
    def is_educational_content(self, video_info: Dict[str, Any], transcript: str) -> Dict[str, Any]:
        """Determine if content is educational using AI analysis"""
        
        analysis_prompt = f"""
        Analyze this YouTube video to determine if it contains educational/study-related content suitable for creating flashcards.

        Video Title: {video_info.get('title', 'N/A')}
        Video Description: {video_info.get('description', '')[:500]}...
        Categories: {', '.join(video_info.get('categories', []))}
        Tags: {', '.join(video_info.get('tags', [])[:10])}
        
        Transcript (first 1000 characters): {transcript[:1000]}...
        
        Analyze if this video is educational and suitable for creating study flashcards. Consider:
        1. Does it teach concepts, facts, or skills?
        2. Is it academic or professional learning content?
        3. Does it contain structured information that can be broken into Q&A format?
        4. Is it tutorial, lecture, or educational content?
        
        IMPORTANT: Respond with ONLY valid JSON:
        {{
            "is_educational": true,
            "confidence": 0.9,
            "reasoning": "explanation of why this is/isn't educational",
            "subject_areas": ["list", "of", "subject", "areas"],
            "difficulty_level": "beginner",
            "suitable_for_flashcards": true
        }}
        """
        
        try:
            response = self.llm.generate(
                user_text=analysis_prompt,
                temperature=0.1,  # Low temperature for consistent analysis
                language="en"
            )
            
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback analysis
                educational_keywords = [
                    'learn', 'teach', 'education', 'tutorial', 'lesson', 'course',
                    'study', 'academic', 'university', 'school', 'training',
                    'explain', 'concept', 'theory', 'practice', 'skill'
                ]
                
                content_text = (video_info.get('title', '') + ' ' + 
                              video_info.get('description', '') + ' ' + 
                              transcript[:1000]).lower()
                
                educational_score = sum(1 for keyword in educational_keywords if keyword in content_text)
                is_educational = educational_score >= 3
                
                return {
                    "is_educational": is_educational,
                    "confidence": min(educational_score / 10, 1.0),
                    "reasoning": f"Found {educational_score} educational keywords",
                    "subject_areas": ["general"],
                    "difficulty_level": "intermediate",
                    "suitable_for_flashcards": is_educational
                }
                
        except Exception as e:
            print(f"Error in educational analysis: {e}")
            return {
                "is_educational": False,
                "confidence": 0.0,
                "reasoning": f"Analysis failed: {str(e)}",
                "subject_areas": [],
                "difficulty_level": "unknown",
                "suitable_for_flashcards": False
            }
    
    def generate_flashcards(self, video_info: Dict[str, Any], transcript: str, 
                          language: str = "en") -> List[Flashcard]:
        """Generate flashcards from educational content"""
        
        flashcard_prompt = f"""
        Create educational flashcards from this YouTube video content. Generate comprehensive question-answer pairs that help students learn and retain the key concepts.

        Video: {video_info.get('title', 'N/A')}
        Subject Areas: {', '.join(video_info.get('categories', []))}
        
        Content Transcript:
        {transcript[:3000]}  # Limit transcript length to avoid token limits
        
        Create 8-12 flashcards covering the main concepts, facts, and learnings from this content. Each flashcard should:
        1. Ask a clear, specific question
        2. Provide a complete, educational answer
        3. Focus on key concepts, definitions, processes, or facts
        4. Be appropriate for the subject matter
        5. Help with active recall and learning
        
        CRITICAL: You must respond with ONLY valid JSON in this exact format. Do not include any explanation text, markdown formatting, or code blocks. Start your response with {{ and end with }}:

        {{
            "flashcards": [
                {{
                    "question": "What is the main concept?",
                    "answer": "The main concept is clearly explained here without quotes or special characters that break JSON.",
                    "category": "General",
                    "difficulty": "medium",
                    "tags": ["concept", "definition"]
                }}
            ]
        }}
        
        IMPORTANT RULES:
        - No text before or after the JSON
        - Use straight quotes only, not curly quotes
        - Escape any quotes inside text with backslash
        - No trailing commas
        - Keep answers concise to avoid JSON parsing issues
        - Maximum 200 characters per answer
        """
        
        try:
            response = self.llm.generate(
                user_text=flashcard_prompt,
                temperature=0.2,  # Slightly creative but consistent
                language=language
            )
            
            print(f"Raw AI response length: {len(response)}")
            
            # Extract JSON from response with better error handling
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                print(f"Extracted JSON length: {len(json_str)}")
                
                try:
                    data = json.loads(json_str)
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                    print(f"Problematic JSON: {json_str[:500]}...")
                    
                    # Try multiple JSON cleaning strategies
                    fixed_json = json_str
                    
                    # Strategy 1: Basic cleaning
                    fixed_json = fixed_json.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
                    
                    # Strategy 2: Remove trailing commas before } or ]
                    fixed_json = re.sub(r',(\s*[}\]])', r'\1', fixed_json)
                    
                    # Strategy 3: Fix common quote issues in answers
                    # Replace problematic quotes in answer values
                    fixed_json = re.sub(r'(:\s*"[^"]*)"([^"]*)"([^"]*")', r'\1"\2\"\3', fixed_json)
                    
                    # Strategy 4: Ensure proper JSON structure
                    if not fixed_json.strip().startswith('{'):
                        # Find the first { and last }
                        start = fixed_json.find('{')
                        end = fixed_json.rfind('}')
                        if start != -1 and end != -1 and end > start:
                            fixed_json = fixed_json[start:end+1]
                    
                    try:
                        data = json.loads(fixed_json)
                        print("Successfully parsed fixed JSON")
                    except json.JSONDecodeError as e2:
                        print(f"Still failed after basic fixing: {e2}")
                        
                        # Strategy 5: More aggressive cleaning - rebuild JSON structure
                        try:
                            # Extract flashcard data using regex
                            flashcard_pattern = r'"question"\s*:\s*"([^"]+)"[^}]*"answer"\s*:\s*"([^"]+)"[^}]*"category"\s*:\s*"([^"]*)"[^}]*"difficulty"\s*:\s*"([^"]*)"'
                            matches = re.findall(flashcard_pattern, json_str, re.DOTALL)
                            
                            if matches:
                                rebuilt_flashcards = []
                                for i, (question, answer, category, difficulty) in enumerate(matches):
                                    # Clean the extracted text
                                    question = question.strip().replace('\\"', '"')
                                    answer = answer.strip().replace('\\"', '"')
                                    category = category.strip() or "General"
                                    difficulty = difficulty.strip() or "medium"
                                    
                                    rebuilt_flashcards.append({
                                        "question": question,
                                        "answer": answer,
                                        "category": category,
                                        "difficulty": difficulty,
                                        "tags": ["extracted"]
                                    })
                                
                                data = {"flashcards": rebuilt_flashcards}
                                print(f"Successfully rebuilt JSON with {len(rebuilt_flashcards)} flashcards")
                            else:
                                print("Failed to extract flashcard data with regex")
                                return []
                        except Exception as e3:
                            print(f"Failed to rebuild JSON: {e3}")
                            return []
                
                flashcards = []
                
                for i, card_data in enumerate(data.get("flashcards", [])):
                    if not isinstance(card_data, dict):
                        continue
                        
                    card = Flashcard(
                        id=f"card_{i+1:03d}",
                        question=card_data.get("question", "").strip(),
                        answer=card_data.get("answer", "").strip(),
                        category=card_data.get("category", "General"),
                        difficulty=card_data.get("difficulty", "medium"),
                        tags=card_data.get("tags", []) if isinstance(card_data.get("tags"), list) else [],
                        status="new",
                        review_count=0,
                        created_at="",  # Will be set when saved
                        last_reviewed=""
                    )
                    
                    # Only add cards with valid content
                    if card.question and card.answer:
                        flashcards.append(card)
                
                print(f"Successfully created {len(flashcards)} flashcards")
                return flashcards
            else:
                print("No JSON found in response")
                print(f"Response preview: {response[:500]}...")
                return []
                
        except Exception as e:
            print(f"Error generating flashcards: {e}")
            # Return empty list if generation fails
            return []
    
    def process_youtube_url(self, url: str, language: str = "en") -> Dict[str, Any]:
        """Main method to process YouTube URL and generate flashcards"""
        try:
            # Extract video ID
            video_id = self.extract_video_id(url)
            if not video_id:
                return {
                    "success": False,
                    "error": "Invalid YouTube URL format",
                    "is_educational": False
                }
            
            # Get video information
            print(f"Getting video info for: {video_id}")
            video_info = self.get_video_info(url)
            
            # Get transcript
            print(f"Getting transcript for: {video_id}")
            transcript = self.get_transcript(video_id)
            
            if len(transcript.strip()) < 100:
                return {
                    "success": False,
                    "error": "Video transcript too short or unavailable",
                    "is_educational": False
                }
            
            # Analyze if educational
            print("Analyzing educational content...")
            educational_analysis = self.is_educational_content(video_info, transcript)
            
            if not educational_analysis.get("is_educational", False):
                return {
                    "success": False,
                    "error": "This video does not appear to contain educational content suitable for flashcards",
                    "is_educational": False,
                    "analysis": educational_analysis
                }
            
            # Generate flashcards
            print("Generating flashcards...")
            flashcards = self.generate_flashcards(video_info, transcript, language)
            
            if not flashcards:
                return {
                    "success": False,
                    "error": "Failed to generate flashcards from content",
                    "is_educational": True,
                    "analysis": educational_analysis
                }
            
            # Create flashcard set
            flashcard_set = FlashcardSet(
                id=f"set_{video_id}",
                title=f"Flashcards: {video_info.get('title', 'Unknown')}",
                description=f"Generated from YouTube video: {video_info.get('title', 'Unknown')}",
                video_url=url,
                video_title=video_info.get('title', 'Unknown'),
                video_duration=str(video_info.get('duration', 0)),
                cards=flashcards,
                created_at=""  # Will be set when saved
            )
            
            return {
                "success": True,
                "is_educational": True,
                "analysis": educational_analysis,
                "flashcard_set": flashcard_set,
                "video_info": video_info
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error processing video: {str(e)}",
                "is_educational": False
            }
    
    def save_flashcard_set(self, flashcard_set: FlashcardSet) -> str:
        """Save flashcard set to local storage"""
        try:
            file_path = self.data_dir / f"{flashcard_set.id}.json"
            
            # Convert to dict for JSON serialization
            data = {
                "id": flashcard_set.id,
                "title": flashcard_set.title,
                "description": flashcard_set.description,
                "video_url": flashcard_set.video_url,
                "video_title": flashcard_set.video_title,
                "video_duration": flashcard_set.video_duration,
                "created_at": flashcard_set.created_at,
                "total_cards": flashcard_set.total_cards,
                "learned_cards": flashcard_set.learned_cards,
                "learning_cards": flashcard_set.learning_cards,
                "cards": [
                    {
                        "id": card.id,
                        "question": card.question,
                        "answer": card.answer,
                        "category": card.category,
                        "difficulty": card.difficulty,
                        "tags": card.tags,
                        "status": card.status,
                        "review_count": card.review_count,
                        "created_at": card.created_at,
                        "last_reviewed": card.last_reviewed
                    }
                    for card in flashcard_set.cards
                ]
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return str(file_path)
            
        except Exception as e:
            raise RuntimeError(f"Failed to save flashcard set: {str(e)}")
    
    def load_flashcard_set(self, set_id: str) -> Optional[FlashcardSet]:
        """Load flashcard set from storage"""
        try:
            file_path = self.data_dir / f"{set_id}.json"
            if not file_path.exists():
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            cards = [
                Flashcard(
                    id=card_data["id"],
                    question=card_data["question"],
                    answer=card_data["answer"],
                    category=card_data["category"],
                    difficulty=card_data["difficulty"],
                    tags=card_data["tags"],
                    status=card_data["status"],
                    review_count=card_data["review_count"],
                    created_at=card_data["created_at"],
                    last_reviewed=card_data["last_reviewed"]
                )
                for card_data in data["cards"]
            ]
            
            return FlashcardSet(
                id=data["id"],
                title=data["title"],
                description=data["description"],
                video_url=data["video_url"],
                video_title=data["video_title"],
                video_duration=data["video_duration"],
                cards=cards,
                created_at=data["created_at"]
            )
            
        except Exception as e:
            print(f"Error loading flashcard set: {e}")
            return None
    
    def list_flashcard_sets(self) -> List[Dict[str, Any]]:
        """List all available flashcard sets"""
        sets = []
        try:
            for file_path in self.data_dir.glob("*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    sets.append({
                        "id": data["id"],
                        "title": data["title"],
                        "description": data["description"],
                        "video_title": data["video_title"],
                        "total_cards": data.get("total_cards", 0),
                        "learned_cards": data.get("learned_cards", 0),
                        "learning_cards": data.get("learning_cards", 0),
                        "created_at": data.get("created_at", "")
                    })
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error listing flashcard sets: {e}")
        
        return sorted(sets, key=lambda x: x.get("created_at", ""), reverse=True)
