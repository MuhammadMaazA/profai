"""
YouTube Playlist Curriculum Generator
Processes YouTube playlists to create structured learning curricula with chapters, notes, and flashcards.
"""

from __future__ import annotations
import re
import json
import uuid
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
import tempfile
import os

import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

from .llm import LLMClient
from .youtube_processor import Flashcard


@dataclass
class Chapter:
    """Individual chapter/video within a curriculum"""
    id: str
    title: str
    description: str
    video_url: str
    video_id: str
    duration: str
    transcript: str
    notes: str = ""
    flashcards: List[Flashcard] = None
    completed: bool = False
    completed_at: str = ""
    order: int = 0

    def __post_init__(self):
        if self.flashcards is None:
            self.flashcards = []


@dataclass
class PlaylistCurriculum:
    """Complete curriculum generated from a YouTube playlist"""
    id: str
    title: str
    description: str
    playlist_url: str
    playlist_id: str
    creator: str
    chapters: List[Chapter]
    total_chapters: int = 0
    completed_chapters: int = 0
    progress_percentage: float = 0.0
    created_at: str = ""
    last_accessed: str = ""
    total_duration: str = ""

    def __post_init__(self):
        self.total_chapters = len(self.chapters)
        self.completed_chapters = sum(1 for chapter in self.chapters if chapter.completed)
        self.progress_percentage = (self.completed_chapters / self.total_chapters * 100) if self.total_chapters > 0 else 0.0


class PlaylistCurriculumProcessor:
    """Handles YouTube playlist processing and curriculum generation"""
    
    def __init__(self):
        self.data_dir = Path("curriculum_data")
        self.data_dir.mkdir(exist_ok=True)
        self.llm = LLMClient()
    
    def extract_playlist_id(self, url: str) -> Optional[str]:
        """Extract playlist ID from YouTube URL"""
        playlist_patterns = [
            r'[?&]list=([a-zA-Z0-9_-]+)',
            r'playlist\?list=([a-zA-Z0-9_-]+)',
            r'/playlist/([a-zA-Z0-9_-]+)'
        ]
        
        for pattern in playlist_patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from YouTube URL"""
        video_patterns = [
            r'(?:v=|/)([0-9A-Za-z_-]{11}).*',
            r'youtu\.be/([0-9A-Za-z_-]{11})',
            r'embed/([0-9A-Za-z_-]{11})'
        ]
        
        for pattern in video_patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def get_playlist_info(self, playlist_url: str) -> Dict[str, Any]:
        """Get playlist metadata and video list using yt-dlp"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'playlist_items': '1-50'  # Limit to first 50 videos
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                playlist_info = ydl.extract_info(playlist_url, download=False)
                
                return {
                    'title': playlist_info.get('title', 'Unknown Playlist'),
                    'description': playlist_info.get('description', ''),
                    'uploader': playlist_info.get('uploader', 'Unknown'),
                    'video_count': playlist_info.get('playlist_count', 0),
                    'videos': playlist_info.get('entries', [])
                }
        except Exception as e:
            print(f"Error extracting playlist info: {e}")
            return {}
    
    def get_video_info(self, video_url: str) -> Dict[str, Any]:
        """Get individual video metadata"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                video_info = ydl.extract_info(video_url, download=False)
                
                duration = video_info.get('duration', 0)
                duration_str = f"{duration // 60}:{duration % 60:02d}" if duration else "Unknown"
                
                return {
                    'title': video_info.get('title', 'Unknown Video'),
                    'description': video_info.get('description', ''),
                    'duration': duration_str,
                    'uploader': video_info.get('uploader', 'Unknown')
                }
        except Exception as e:
            print(f"Error extracting video info: {e}")
            return {
                'title': 'Unknown Video',
                'description': '',
                'duration': 'Unknown',
                'uploader': 'Unknown'
            }
    
    def get_transcript(self, video_id: str) -> str:
        """Get video transcript"""
        try:
            # Create API instance
            api = YouTubeTranscriptApi()
            
            # Try to get transcript
            transcript_data = api.fetch(video_id)
            formatter = TextFormatter()
            transcript = formatter.format_transcript(transcript_data)
            return transcript.strip()
        except Exception as e:
            print(f"Error getting transcript for {video_id}: {e}")
            return ""
    
    def generate_chapter_notes(self, chapter: Chapter) -> str:
        """Generate comprehensive notes for a chapter using LLM"""
        if not chapter.transcript and not chapter.description:
            return "No content available for generating notes."
        
        # Use transcript if available, otherwise use title and description
        content_source = chapter.transcript if chapter.transcript else f"Title: {chapter.title}\n\nDescription: {chapter.description}"
        
        prompt = f"""
        Create comprehensive study notes for this video chapter titled "{chapter.title}".
        
        Video Content:
        {content_source}
        
        Generate detailed, well-structured notes that include:
        1. Main concepts and key points
        2. Important definitions and terminology
        3. Step-by-step explanations where applicable
        4. Examples and practical applications
        5. Summary of key takeaways
        
        Format the notes in markdown with clear headers, bullet points, and sections.
        Make them suitable for studying and review.
        
        If the content is limited, focus on what can be inferred from the title and create educational context around the topic.
        """
        
        try:
            notes = self.llm.generate(
                user_text=prompt,
                emotion='focused',
                language='en'
            )
            return notes
        except Exception as e:
            print(f"Error generating notes: {e}")
            return "Failed to generate notes for this chapter."
    
    def generate_chapter_flashcards(self, chapter: Chapter) -> List[Flashcard]:
        """Generate flashcards for a chapter using LLM"""
        if not chapter.transcript and not chapter.description:
            return []
        
        # Use transcript if available, otherwise use title and description
        content_source = chapter.transcript if chapter.transcript else f"Title: {chapter.title}\n\nDescription: {chapter.description}"
        
        prompt = f"""
        Create educational flashcards for this video chapter titled "{chapter.title}".
        
        Video Content:
        {content_source}
        
        Generate 6-10 high-quality flashcards that cover:
        1. Key concepts and definitions
        2. Important facts and figures
        3. Process steps or procedures
        4. Examples and applications
        5. Critical thinking questions
        
        Format each flashcard exactly as:
        Q: [Clear, specific question]
        A: [Comprehensive but concise answer]
        Category: [Subject area]
        Difficulty: [easy/medium/hard]
        Tags: [relevant keywords separated by commas]
        
        Separate each flashcard with "---"
        
        If content is limited, create flashcards based on the topic suggested by the title.
        """
        
        try:
            response = self.llm.generate(
                user_text=prompt,
                emotion='focused',
                language='en'
            )
            
            return self.parse_flashcards_from_response(response, chapter.title)
        except Exception as e:
            print(f"Error generating flashcards: {e}")
            return []
    
    def parse_flashcards_from_response(self, response: str, chapter_title: str) -> List[Flashcard]:
        """Parse LLM response into flashcard objects"""
        flashcards = []
        cards_text = response.split('---')
        
        for i, card_text in enumerate(cards_text):
            if not card_text.strip():
                continue
                
            try:
                lines = [line.strip() for line in card_text.strip().split('\n') if line.strip()]
                
                question = ""
                answer = ""
                category = chapter_title
                difficulty = "medium"
                tags = []
                
                for line in lines:
                    if line.startswith('Q:'):
                        question = line[2:].strip()
                    elif line.startswith('A:'):
                        answer = line[2:].strip()
                    elif line.startswith('Category:'):
                        category = line[9:].strip()
                    elif line.startswith('Difficulty:'):
                        difficulty = line[11:].strip().lower()
                    elif line.startswith('Tags:'):
                        tags = [tag.strip() for tag in line[5:].split(',')]
                
                if question and answer:
                    flashcard = Flashcard(
                        id=str(uuid.uuid4()),
                        question=question,
                        answer=answer,
                        category=category,
                        difficulty=difficulty,
                        tags=tags,
                        created_at=datetime.now().isoformat()
                    )
                    flashcards.append(flashcard)
                    
            except Exception as e:
                print(f"Error parsing flashcard {i}: {e}")
                continue
        
        return flashcards
    
    def process_playlist(self, playlist_url: str) -> Dict[str, Any]:
        """Main method to process a YouTube playlist and create curriculum"""
        try:
            # Extract playlist ID
            playlist_id = self.extract_playlist_id(playlist_url)
            if not playlist_id:
                return {
                    "success": False,
                    "error": "Invalid YouTube playlist URL format"
                }
            
            # Get playlist information
            print(f"Processing playlist: {playlist_id}")
            playlist_info = self.get_playlist_info(playlist_url)
            
            if not playlist_info:
                return {
                    "success": False,
                    "error": "Could not retrieve playlist information"
                }
            
            print(f"Found playlist: {playlist_info['title']} with {len(playlist_info.get('videos', []))} videos")
            
            # Create curriculum structure
            curriculum_id = str(uuid.uuid4())
            chapters = []
            total_duration_seconds = 0
            
            # Process each video in the playlist
            videos_to_process = playlist_info['videos'][:10]  # Limit to 10 videos for faster processing
            print(f"Processing {len(videos_to_process)} videos...")
            
            for i, video_entry in enumerate(videos_to_process):
                video_id = video_entry.get('id')
                if not video_id:
                    print(f"Skipping video {i+1}: No video ID found")
                    continue
                
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                print(f"Processing video {i+1}/{len(videos_to_process)}: {video_id}")
                
                try:
                    # Get video info and transcript
                    video_info = self.get_video_info(video_url)
                    print(f"Got video info: {video_info['title']}")
                    
                    transcript = self.get_transcript(video_id)
                    if transcript:
                        print(f"Got transcript: {len(transcript)} characters")
                    else:
                        print(f"No transcript available for video {video_id}")
                    
                    # Create chapter even if no transcript
                    chapter = Chapter(
                        id=str(uuid.uuid4()),
                        title=video_info['title'],
                        description=video_info['description'][:500] + "..." if len(video_info['description']) > 500 else video_info['description'],
                        video_url=video_url,
                        video_id=video_id,
                        duration=video_info['duration'],
                        transcript=transcript,
                        order=i + 1
                    )
                    
                    # Always generate notes and flashcards (use transcript if available, otherwise use title/description)
                    print(f"Generating content for chapter: {chapter.title}")
                    try:
                        chapter.notes = self.generate_chapter_notes(chapter)
                        chapter.flashcards = self.generate_chapter_flashcards(chapter)
                        print(f"Generated {len(chapter.flashcards)} flashcards")
                    except Exception as e:
                        print(f"Error generating content for chapter {chapter.title}: {e}")
                        chapter.notes = f"Content generation failed: {str(e)}"
                        chapter.flashcards = []
                        chapter.flashcards = []
                    
                    chapters.append(chapter)
                    print(f"Added chapter: {chapter.title}")
                    
                except Exception as e:
                    print(f"Error processing video {video_id}: {e}")
                    continue
            
            # Create curriculum
            curriculum = PlaylistCurriculum(
                id=curriculum_id,
                title=playlist_info['title'],
                description=playlist_info['description'][:1000] + "..." if len(playlist_info['description']) > 1000 else playlist_info['description'],
                playlist_url=playlist_url,
                playlist_id=playlist_id,
                creator=playlist_info['uploader'],
                chapters=chapters,
                created_at=datetime.now().isoformat(),
                last_accessed=datetime.now().isoformat(),
                total_duration=f"{len(chapters)} chapters"
            )
            
            # Save curriculum
            self.save_curriculum(curriculum)
            
            return {
                "success": True,
                "curriculum_id": curriculum_id,
                "title": curriculum.title,
                "chapters": len(chapters),
                "message": f"Successfully created curriculum with {len(chapters)} chapters"
            }
            
        except Exception as e:
            print(f"Error processing playlist: {e}")
            return {
                "success": False,
                "error": f"Error processing playlist: {str(e)}"
            }
    
    def save_curriculum(self, curriculum: PlaylistCurriculum):
        """Save curriculum to JSON file"""
        file_path = self.data_dir / f"{curriculum.id}.json"
        
        # Convert dataclass to dict for JSON serialization
        curriculum_dict = asdict(curriculum)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(curriculum_dict, f, indent=2, ensure_ascii=False)
    
    def load_curriculum(self, curriculum_id: str) -> Optional[PlaylistCurriculum]:
        """Load curriculum from JSON file"""
        file_path = self.data_dir / f"{curriculum_id}.json"
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert dict back to dataclass
            chapters = []
            for chapter_data in data.get('chapters', []):
                flashcards = []
                for card_data in chapter_data.get('flashcards', []):
                    flashcard = Flashcard(**card_data)
                    flashcards.append(flashcard)
                
                chapter_data['flashcards'] = flashcards
                chapter = Chapter(**chapter_data)
                chapters.append(chapter)
            
            data['chapters'] = chapters
            curriculum = PlaylistCurriculum(**data)
            return curriculum
            
        except Exception as e:
            print(f"Error loading curriculum: {e}")
            return None
    
    def list_curricula(self) -> List[Dict[str, Any]]:
        """List all available curricula"""
        curricula = []
        
        for file_path in self.data_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                curriculum_summary = {
                    'id': data.get('id'),
                    'title': data.get('title'),
                    'description': data.get('description', '')[:200] + "..." if len(data.get('description', '')) > 200 else data.get('description', ''),
                    'creator': data.get('creator'),
                    'total_chapters': data.get('total_chapters', 0),
                    'completed_chapters': data.get('completed_chapters', 0),
                    'progress_percentage': data.get('progress_percentage', 0),
                    'created_at': data.get('created_at'),
                    'last_accessed': data.get('last_accessed')
                }
                curricula.append(curriculum_summary)
                
            except Exception as e:
                print(f"Error reading curriculum file {file_path}: {e}")
                continue
        
        # Sort by last accessed (most recent first)
        curricula.sort(key=lambda x: x.get('last_accessed', ''), reverse=True)
        return curricula
    
    def update_chapter_progress(self, curriculum_id: str, chapter_id: str, completed: bool) -> bool:
        """Update chapter completion status"""
        curriculum = self.load_curriculum(curriculum_id)
        if not curriculum:
            return False
        
        for chapter in curriculum.chapters:
            if chapter.id == chapter_id:
                chapter.completed = completed
                if completed:
                    chapter.completed_at = datetime.now().isoformat()
                else:
                    chapter.completed_at = ""
                break
        
        # Update curriculum progress
        curriculum.completed_chapters = sum(1 for chapter in curriculum.chapters if chapter.completed)
        curriculum.progress_percentage = (curriculum.completed_chapters / curriculum.total_chapters * 100) if curriculum.total_chapters > 0 else 0.0
        curriculum.last_accessed = datetime.now().isoformat()
        
        # Save updated curriculum
        self.save_curriculum(curriculum)
        return True
    
    def delete_curriculum(self, curriculum_id: str) -> bool:
        """Delete a curriculum"""
        file_path = self.data_dir / f"{curriculum_id}.json"
        
        try:
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception as e:
            print(f"Error deleting curriculum: {e}")
            return False
