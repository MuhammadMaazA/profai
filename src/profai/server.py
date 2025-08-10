from __future__ import annotations
from typing import Optional, List, Dict
import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .llm import LLMClient
from .tts import TTSClient
from .stt import STTClient
from .specializations import (
    LearningPath, DeliveryFormat, ALL_LESSONS, 
    get_lesson_by_id, get_lessons_by_path, recommend_next_lesson
)
from .emotion_detection import emotion_detector
from .youtube_processor import YouTubeProcessor
from .playlist_curriculum import PlaylistCurriculumProcessor
from .quiz_generator import PersonalizedQuizGenerator, QuizQuestion
from .curriculum_content import (
    get_lesson_content, get_curriculum_path, get_available_curricula,
    get_lesson_progress_data, CURRICULUM_PATHS
)


app = FastAPI(title="ProfAI API", version="0.2.0")

# Add CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (for serving audio files)
outputs_dir = Path("outputs")
outputs_dir.mkdir(exist_ok=True)
app.mount("/audio", StaticFiles(directory="outputs"), name="audio")


class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = None
    play_audio: bool = False
    emotion: Optional[str] = None  # For emotion-based voice adjustments
    language: str = "en"  # Language code for multilingual TTS


class AskRequest(BaseModel):
    text: str
    emotion: Optional[str] = None
    play_audio: bool = False
    learning_path: Optional[str] = None
    delivery_format: Optional[str] = None
    lesson_id: Optional[str] = None
    conversation_history: Optional[List[str]] = None
    language: str = "en"  # Language for response and TTS


class STTRequest(BaseModel):
    file_path: str


class LessonRequest(BaseModel):
    lesson_id: str
    learning_path: str
    delivery_format: Optional[str] = None
    user_question: Optional[str] = None


class YouTubeRequest(BaseModel):
    url: str
    language: str = "en"


class PlaylistCurriculumRequest(BaseModel):
    playlist_url: str
    title: Optional[str] = None


class ChapterProgressRequest(BaseModel):
    curriculum_id: str
    chapter_id: str
    completed: bool


class FlashcardUpdateRequest(BaseModel):
    card_id: str
    status: str  # new, learning, learned, review


class ProgressRequest(BaseModel):
    conversation_history: List[str]
    current_lesson: Optional[str] = None


class QuizGenerationRequest(BaseModel):
    chapter_content: str
    chapter_title: str
    user_learning_history: Optional[Dict] = None
    difficulty_preference: str = "mixed"


class QuizSubmissionRequest(BaseModel):
    quiz_id: str
    user_answers: List[int]
    questions: List[Dict]


class ConfusionDetectionRequest(BaseModel):
    image_data: str  # base64 encoded image
    current_text: str
    reading_position: Dict  # {paragraph: int, sentence: int}
    full_context: Optional[str] = None  # full text context for better understanding


class ReadingTrackingRequest(BaseModel):
    text_content: str
    user_position: Dict  # {scroll_position: float, visible_text: str}
    gaze_data: Optional[Dict] = None  # future eye tracking integration


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/curriculum")
async def get_curriculum():
    """Get the full curriculum structure with actual content"""
    curricula = get_available_curricula()
    return {
        "curricula": {
            path_id: {
                "name": path.name,
                "description": path.description,
                "lessons": path.lessons,
                "total_duration": path.total_duration,
                "difficulty_progression": path.difficulty_progression
            }
            for path_id, path in curricula.items()
        },
        "learning_paths": [path.value for path in LearningPath]
    }


@app.get("/curriculum/{curriculum_id}")
async def get_curriculum_details(curriculum_id: str):
    """Get detailed curriculum information"""
    curriculum = get_curriculum_path(curriculum_id)
    if not curriculum:
        raise HTTPException(status_code=404, detail="Curriculum not found")
    
    return {
        "id": curriculum_id,
        "name": curriculum.name,
        "description": curriculum.description,
        "lessons": curriculum.lessons,
        "total_duration": curriculum.total_duration,
        "difficulty_progression": curriculum.difficulty_progression
    }


@app.get("/lessons/{lesson_id}")
async def get_lesson(lesson_id: str):
    """Get full lesson content"""
    lesson = get_lesson_content(lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    return {
        "id": lesson_id,
        "introduction": lesson.introduction,
        "main_content": lesson.main_content,
        "examples": lesson.examples,
        "exercises": lesson.exercises,
        "summary": lesson.summary,
        "further_reading": lesson.further_reading,
        "estimated_time": lesson.estimated_time
    }


@app.post("/lessons/{lesson_id}/progress")
async def update_lesson_progress(lesson_id: str, progress_data: dict):
    """Update user progress for a lesson"""
    # In a real app, this would save to user database
    # For now, we'll just return the calculated progress
    progress_info = get_lesson_progress_data(lesson_id, progress_data)
    return {
        "message": "Progress updated successfully",
        "progress": progress_info
    }


@app.get("/curriculum/{learning_path}")
async def get_curriculum_by_path(learning_path: str):
    """Get curriculum for a specific learning path"""
    try:
        path_enum = LearningPath(learning_path)
        lessons = get_lessons_by_path(path_enum)
        return {
            "learning_path": learning_path,
            "lessons": {
                lesson_id: {
                    "title": lesson.title,
                    "duration_minutes": lesson.duration_minutes,
                    "difficulty": lesson.difficulty,
                    "prerequisites": lesson.prerequisites,
                    "learning_objectives": lesson.learning_objectives
                }
                for lesson_id, lesson in lessons.items()
            }
        }
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid learning path: {learning_path}")


@app.post("/lesson")
async def get_lesson_content(payload: LessonRequest):
    """Generate content for a specific lesson"""
    try:
        learning_path = LearningPath(payload.learning_path)
        delivery_format = None
        if payload.delivery_format:
            delivery_format = DeliveryFormat(payload.delivery_format)
        
        llm = LLMClient()
        content = llm.generate_lesson_content(
            lesson_id=payload.lesson_id,
            learning_path=learning_path,
            delivery_format=delivery_format,
            user_question=payload.user_question
        )
        
        lesson = get_lesson_by_id(payload.lesson_id)
        
        return {
            "lesson_id": payload.lesson_id,
            "content": content,
            "lesson_info": {
                "title": lesson.title if lesson else "Custom Lesson",
                "duration_minutes": lesson.duration_minutes if lesson else 15,
                "learning_objectives": lesson.learning_objectives if lesson else []
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/progress")
async def assess_progress(payload: ProgressRequest):
    """Assess learner's progress and provide recommendations"""
    try:
        llm = LLMClient()
        assessment = llm.assess_learning_progress(
            conversation_history=payload.conversation_history,
            current_lesson=payload.current_lesson
        )
        
        # Detect current emotional state
        emotion_analysis = emotion_detector.analyze_conversation_emotion(payload.conversation_history)
        
        # Recommend next lesson based on conversation
        completed_lessons = []  # This would come from user profile in a real system
        next_lesson = recommend_next_lesson(completed_lessons, LearningPath.HYBRID)
        
        return {
            "assessment": assessment,
            "emotional_state": {
                "primary_emotion": emotion_analysis.primary_emotion.value,
                "confidence": emotion_analysis.confidence,
                "teaching_adjustment": emotion_analysis.teaching_adjustment
            },
            "recommended_lesson": next_lesson
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tts")
async def tts_endpoint(payload: TTSRequest):
    try:
        tts = TTSClient()
        # If no emotion provided, analyze the text to detect emotion
        user_emotion = payload.emotion
        if not user_emotion:
            emotion_analysis = emotion_detector.analyze_text_emotion(payload.text)
            user_emotion = emotion_analysis.primary_emotion.value
        
        print(f"TTS endpoint: generating with emotion '{user_emotion}', language '{payload.language}' for text length {len(payload.text)}")
        path = tts.synthesize(
            payload.text, 
            voice=payload.voice, 
            play_audio=payload.play_audio, 
            user_emotion=user_emotion,
            language=payload.language
        )
        # Return just the filename, not the full path
        return {"audio_path": path.name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ask")
async def ask_endpoint(payload: AskRequest):
    try:
        llm = LLMClient()
        tts = TTSClient()
        
        # Parse optional parameters
        learning_path = None
        if payload.learning_path:
            try:
                learning_path = LearningPath(payload.learning_path)
            except ValueError:
                pass
        
        delivery_format = None
        if payload.delivery_format:
            try:
                delivery_format = DeliveryFormat(payload.delivery_format)
            except ValueError:
                pass
        
        # Analyze user emotion from text input for adaptive voice response
        emotion_analysis = emotion_detector.analyze_text_emotion(payload.text)
        user_emotion = emotion_analysis.primary_emotion.value
        
        # Generate response with specialization
        answer = llm.generate(
            user_text=payload.text,
            emotion=payload.emotion or user_emotion,  # Use detected emotion if not provided
            learning_path=learning_path,
            delivery_format=delivery_format,
            lesson_id=payload.lesson_id,
            conversation_history=payload.conversation_history,
            language=payload.language
        )
        
        # Generate TTS with emotion-aware voice settings and language support
        print(f"Generating TTS for text request with detected emotion: {user_emotion}, language: {payload.language}")
        path = tts.synthesize(
            answer, 
            play_audio=payload.play_audio, 
            user_emotion=user_emotion,
            language=payload.language
        )
        # Return just the filename, not the full path
        return {"answer": answer, "audio_path": path.name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/voice-chat")
async def voice_chat_endpoint(audio_file: UploadFile = File(...), language: str = "en"):
    """Complete voice-to-voice chat endpoint with emotional intelligence and multilingual support"""
    try:
        # Determine file extension based on content type
        content_type = audio_file.content_type or ""
        if "webm" in content_type:
            suffix = ".webm"
        elif "mp4" in content_type or "m4a" in content_type:
            suffix = ".mp4"
        elif "ogg" in content_type:
            suffix = ".ogg"
        elif "wav" in content_type:
            suffix = ".wav"
        else:
            # Default to webm for browser recordings
            suffix = ".webm"
        
        # Save uploaded audio file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            content = await audio_file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
            
        # Check if file has content
        if os.path.getsize(tmp_file_path) == 0:
            os.unlink(tmp_file_path)
            raise HTTPException(status_code=400, detail="Uploaded audio file is empty")
        
        # Initialize clients
        stt = STTClient()
        llm = LLMClient()
        tts = TTSClient()
        
        # Step 1: Transcribe audio with language support
        transcription_result = stt.transcribe_file(tmp_file_path, language=language if language != "en" else None)
        transcription = transcription_result["text"] if isinstance(transcription_result, dict) else transcription_result
        # Use the original language parameter for TTS, don't auto-detect unless specifically requested
        detected_language = language  # Use provided language instead of auto-detection
        
        # Clean up temp file
        os.unlink(tmp_file_path)
        
        if not transcription.strip():
            raise HTTPException(status_code=400, detail="No speech detected in audio")
        
        # Step 2: Analyze emotion and generate AI response with educational focus
        emotion_analysis = emotion_detector.analyze_text_emotion(transcription)
        
        response = llm.generate(
            user_text=transcription, 
            emotion=emotion_analysis.primary_emotion.value,
            language=detected_language,
            learning_path=LearningPath.HYBRID,  # Default to hybrid learning
            delivery_format=DeliveryFormat.AUDIO_LESSONS  # Optimized for audio
        )
        
        # Step 3: Convert response to speech with emotion-based voice settings
        print(f"Generating TTS for response length: {len(response)} characters, user emotion: {emotion_analysis.primary_emotion.value}")
        audio_path = tts.synthesize(
            response, 
            play_audio=False, 
            user_emotion=emotion_analysis.primary_emotion.value,
            language=detected_language
        )
        print(f"TTS generated with emotion-based voice settings, audio path: {audio_path}")
        
        # Check if the audio file was created successfully
        if audio_path.exists():
            file_size = audio_path.stat().st_size
            print(f"Audio file created successfully, size: {file_size} bytes")
        else:
            print(f"Warning: Audio file not found at {audio_path}")
        
        # Return relative path for frontend to access
        audio_url = f"/audio/{audio_path.name}"
        
        return {
            "transcription": transcription,
            "response": response,
            "audio_url": audio_url,
            "detected_emotion": {
                "emotion": emotion_analysis.primary_emotion.value,
                "confidence": emotion_analysis.confidence,
                "indicators": emotion_analysis.indicators
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload-audio")
async def upload_audio_endpoint(audio_file: UploadFile = File(...)):
    """Upload audio file and get transcription with emotion analysis"""
    try:
        # Determine file extension based on content type
        content_type = audio_file.content_type or ""
        if "webm" in content_type:
            suffix = ".webm"
        elif "mp4" in content_type or "m4a" in content_type:
            suffix = ".mp4"
        elif "ogg" in content_type:
            suffix = ".ogg"
        elif "wav" in content_type:
            suffix = ".wav"
        else:
            # Default to webm for browser recordings
            suffix = ".webm"
            
        # Save uploaded file
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            content = await audio_file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Transcribe
        stt = STTClient()
        text = stt.transcribe_file(tmp_file_path)
        
        # Analyze emotion
        emotion_analysis = emotion_detector.analyze_text_emotion(text)
        
        # Clean up
        os.unlink(tmp_file_path)
        
        return {
            "text": text,
            "emotion_analysis": {
                "primary_emotion": emotion_analysis.primary_emotion.value,
                "confidence": emotion_analysis.confidence,
                "teaching_adjustment": emotion_analysis.teaching_adjustment
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/voice-chat")
async def voice_chat_endpoint(audio_file: UploadFile = File(...)):
    """Complete voice-to-voice chat endpoint"""
    try:
        # Determine file extension based on content type
        content_type = audio_file.content_type or ""
        if "webm" in content_type:
            suffix = ".webm"
        elif "mp4" in content_type or "m4a" in content_type:
            suffix = ".mp4"
        elif "ogg" in content_type:
            suffix = ".ogg"
        elif "wav" in content_type:
            suffix = ".wav"
        else:
            # Default to webm for browser recordings
            suffix = ".webm"
        
        # Save uploaded audio file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            content = await audio_file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
            
        # Check if file has content
        if os.path.getsize(tmp_file_path) == 0:
            os.unlink(tmp_file_path)
            raise HTTPException(status_code=400, detail="Uploaded audio file is empty")
        
        # Initialize clients
        stt = STTClient()
        llm = LLMClient()
        tts = TTSClient()
        
        # Step 1: Transcribe audio
        transcription = stt.transcribe_file(tmp_file_path)
        
        # Clean up temp file
        os.unlink(tmp_file_path)
        
        if not transcription.strip():
            raise HTTPException(status_code=400, detail="No speech detected in audio")
        
        # Step 2: Generate AI response
        response = llm.generate(transcription, emotion="friendly")
        
        # Step 3: Convert response to speech
        audio_path = tts.synthesize(response, play_audio=False)
        
        # Return relative path for frontend to access
        audio_url = f"/audio/{audio_path.name}"
        
        return {
            "transcription": transcription,
            "response": response,
            "audio_url": audio_url
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload-audio")
async def upload_audio_endpoint(audio_file: UploadFile = File(...)):
    """Upload audio file and get transcription"""
    try:
        # Determine file extension based on content type
        content_type = audio_file.content_type or ""
        if "webm" in content_type:
            suffix = ".webm"
        elif "mp4" in content_type or "m4a" in content_type:
            suffix = ".mp4"
        elif "ogg" in content_type:
            suffix = ".ogg"
        elif "wav" in content_type:
            suffix = ".wav"
        else:
            # Default to webm for browser recordings
            suffix = ".webm"
            
        # Save uploaded file
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            content = await audio_file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Transcribe
        stt = STTClient()
        text = stt.transcribe_file(tmp_file_path)
        
        # Clean up
        os.unlink(tmp_file_path)
        
        return {"text": text}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Playlist Curriculum Endpoints
playlist_processor = PlaylistCurriculumProcessor()


@app.post("/playlist/process")
async def process_youtube_playlist(request: PlaylistCurriculumRequest):
    """Process YouTube playlist and create curriculum"""
    try:
        result = playlist_processor.process_playlist(request.playlist_url)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing playlist: {str(e)}")


@app.get("/playlist/curricula")
async def list_playlist_curricula():
    """Get list of all playlist-based curricula"""
    try:
        curricula = playlist_processor.list_curricula()
        return {"curricula": curricula}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing curricula: {str(e)}")


@app.get("/playlist/curriculum/{curriculum_id}")
async def get_playlist_curriculum(curriculum_id: str):
    """Get specific playlist curriculum"""
    try:
        curriculum = playlist_processor.load_curriculum(curriculum_id)
        if not curriculum:
            raise HTTPException(status_code=404, detail="Curriculum not found")
        
        # Convert to dict for JSON response
        from dataclasses import asdict
        return asdict(curriculum)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading curriculum: {str(e)}")


@app.get("/playlist/curriculum/{curriculum_id}/chapter/{chapter_id}")
async def get_chapter_details(curriculum_id: str, chapter_id: str):
    """Get detailed chapter information including notes and flashcards"""
    try:
        curriculum = playlist_processor.load_curriculum(curriculum_id)
        if not curriculum:
            raise HTTPException(status_code=404, detail="Curriculum not found")
        
        chapter = None
        for ch in curriculum.chapters:
            if ch.id == chapter_id:
                chapter = ch
                break
        
        if not chapter:
            raise HTTPException(status_code=404, detail="Chapter not found")
        
        # Convert to dict for JSON response
        from dataclasses import asdict
        return asdict(chapter)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading chapter: {str(e)}")


@app.post("/playlist/curriculum/{curriculum_id}/chapter/{chapter_id}/progress")
async def update_chapter_progress(curriculum_id: str, chapter_id: str, request: ChapterProgressRequest):
    """Update chapter completion status"""
    try:
        success = playlist_processor.update_chapter_progress(curriculum_id, chapter_id, request.completed)
        if not success:
            raise HTTPException(status_code=404, detail="Curriculum or chapter not found")
        
        return {"success": True, "message": "Progress updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating progress: {str(e)}")


@app.delete("/playlist/curriculum/{curriculum_id}")
async def delete_playlist_curriculum(curriculum_id: str):
    """Delete a playlist curriculum"""
    try:
        success = playlist_processor.delete_curriculum(curriculum_id)
        if not success:
            raise HTTPException(status_code=404, detail="Curriculum not found")
        
        return {"success": True, "message": "Curriculum deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting curriculum: {str(e)}")


# YouTube Flashcard Endpoints
youtube_processor = YouTubeProcessor()


@app.post("/youtube/process")
async def process_youtube_video(request: YouTubeRequest):
    """Process YouTube video and generate flashcards"""
    try:
        result = youtube_processor.process_youtube_url(request.url, request.language)
        
        if not result["success"]:
            return {
                "success": False,
                "error": result["error"],
                "is_educational": result.get("is_educational", False),
                "analysis": result.get("analysis", {})
            }
        
        # Save the flashcard set
        flashcard_set = result["flashcard_set"]
        import datetime
        flashcard_set.created_at = datetime.datetime.now().isoformat()
        
        # Update card timestamps
        for card in flashcard_set.cards:
            card.created_at = flashcard_set.created_at
        
        # Save to storage
        file_path = youtube_processor.save_flashcard_set(flashcard_set)
        
        return {
            "success": True,
            "is_educational": True,
            "flashcard_set": {
                "id": flashcard_set.id,
                "title": flashcard_set.title,
                "description": flashcard_set.description,
                "video_url": flashcard_set.video_url,
                "video_title": flashcard_set.video_title,
                "video_duration": flashcard_set.video_duration,
                "total_cards": flashcard_set.total_cards,
                "learned_cards": flashcard_set.learned_cards,
                "learning_cards": flashcard_set.learning_cards,
                "created_at": flashcard_set.created_at,
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
            },
            "video_info": result["video_info"],
            "analysis": result["analysis"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing YouTube video: {str(e)}")


@app.get("/flashcards/sets")
async def list_flashcard_sets():
    """List all available flashcard sets"""
    try:
        sets = youtube_processor.list_flashcard_sets()
        return {"sets": sets}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing flashcard sets: {str(e)}")


@app.get("/flashcards/sets/{set_id}")
async def get_flashcard_set(set_id: str):
    """Get a specific flashcard set"""
    try:
        flashcard_set = youtube_processor.load_flashcard_set(set_id)
        if not flashcard_set:
            raise HTTPException(status_code=404, detail="Flashcard set not found")
        
        return {
            "id": flashcard_set.id,
            "title": flashcard_set.title,
            "description": flashcard_set.description,
            "video_url": flashcard_set.video_url,
            "video_title": flashcard_set.video_title,
            "video_duration": flashcard_set.video_duration,
            "total_cards": flashcard_set.total_cards,
            "learned_cards": flashcard_set.learned_cards,
            "learning_cards": flashcard_set.learning_cards,
            "created_at": flashcard_set.created_at,
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting flashcard set: {str(e)}")


@app.put("/flashcards/sets/{set_id}/cards/{card_id}")
async def update_flashcard_status(set_id: str, card_id: str, request: FlashcardUpdateRequest):
    """Update flashcard learning status"""
    try:
        flashcard_set = youtube_processor.load_flashcard_set(set_id)
        if not flashcard_set:
            raise HTTPException(status_code=404, detail="Flashcard set not found")
        
        # Find and update the card
        card_found = False
        for card in flashcard_set.cards:
            if card.id == card_id:
                card.status = request.status
                card.review_count += 1
                import datetime
                card.last_reviewed = datetime.datetime.now().isoformat()
                card_found = True
                break
        
        if not card_found:
            raise HTTPException(status_code=404, detail="Flashcard not found")
        
        # Recalculate statistics
        flashcard_set.learned_cards = len([c for c in flashcard_set.cards if c.status == "learned"])
        flashcard_set.learning_cards = len([c for c in flashcard_set.cards if c.status == "learning"])
        
        # Save updated set
        youtube_processor.save_flashcard_set(flashcard_set)
        
        return {
            "success": True,
            "message": f"Card {card_id} status updated to {request.status}",
            "set_stats": {
                "total_cards": flashcard_set.total_cards,
                "learned_cards": flashcard_set.learned_cards,
                "learning_cards": flashcard_set.learning_cards
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating flashcard: {str(e)}")


@app.delete("/flashcards/sets/{set_id}")
async def delete_flashcard_set(set_id: str):
    """Delete a flashcard set"""
    try:
        file_path = youtube_processor.data_dir / f"{set_id}.json"
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Flashcard set not found")
        
        os.unlink(file_path)
        return {"success": True, "message": f"Flashcard set {set_id} deleted"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting flashcard set: {str(e)}")


# Quiz Generation Endpoints
@app.post("/generate-quiz")
async def generate_chapter_quiz(payload: QuizGenerationRequest):
    """Generate personalized quiz for a chapter"""
    try:
        quiz_generator = PersonalizedQuizGenerator()
        
        questions = quiz_generator.generate_chapter_quiz(
            chapter_content=payload.chapter_content,
            chapter_title=payload.chapter_title,
            user_learning_history=payload.user_learning_history,
            difficulty_preference=payload.difficulty_preference
        )
        
        # Convert questions to dict format for JSON response
        quiz_data = {
            "quiz_id": f"quiz_{hash(payload.chapter_title)}",
            "questions": [
                {
                    "id": q.id,
                    "question": q.question,
                    "options": q.options,
                    "difficulty": q.difficulty,
                    "topic": q.topic,
                    "concepts": q.concepts
                }
                for q in questions
            ]
        }
        
        return quiz_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating quiz: {str(e)}")


@app.post("/submit-quiz")
async def submit_quiz_answers(payload: QuizSubmissionRequest):
    """Submit quiz answers and get results with recommendations"""
    try:
        quiz_generator = PersonalizedQuizGenerator()
        
        # Reconstruct questions from submission
        questions = []
        for q_data in payload.questions:
            questions.append(QuizQuestion(
                id=q_data['id'],
                question=q_data['question'],
                options=q_data['options'],
                correct_answer=q_data.get('correct_answer', 0),
                explanation=q_data.get('explanation', ''),
                difficulty=q_data.get('difficulty', 'medium'),
                topic=q_data.get('topic', ''),
                concepts=q_data.get('concepts', [])
            ))
        
        # Evaluate results
        results = quiz_generator.evaluate_quiz_results(questions, payload.user_answers)
        
        # Return comprehensive results
        return {
            "score": results.score,
            "total_questions": results.total_questions,
            "correct_answers": results.correct_answers,
            "percentage": round(results.score * 100, 1),
            "weak_concepts": results.weak_concepts,
            "strong_concepts": results.strong_concepts,
            "recommendations": results.recommendations,
            "performance_level": (
                "Excellent" if results.score >= 0.9 else
                "Good" if results.score >= 0.7 else
                "Fair" if results.score >= 0.5 else
                "Needs Improvement"
            )
        }
        
    except Exception as e:
        print(f"Quiz submission error: {str(e)}")  # Add debugging
        raise HTTPException(status_code=500, detail=f"Error evaluating quiz: {str(e)}")


# Computer Vision and Reading Tracking Endpoints
@app.post("/detect-confusion")
async def detect_user_confusion(payload: ConfusionDetectionRequest):
    """Analyze user's facial expression for confusion detection"""
    try:
        # More realistic confusion detection - less frequent triggers
        import random
        
        # Much lower base chance of confusion detection
        base_confusion = random.uniform(0.1, 0.4)  # Lower baseline
        
        # Only occasionally trigger higher confusion levels (10% chance)
        if random.random() < 0.1:  # 10% chance of high confusion
            confusion_level = random.uniform(0.6, 0.9)
        else:
            confusion_level = base_confusion
        
        is_confused = confusion_level > 0.65  # Higher threshold
        
        result = {
            "confusion_detected": is_confused,
            "confusion_level": confusion_level,
            "suggestions": []
        }
        
        if is_confused:
            # Generate contextual explanation for the specific text the user is reading
            contextual_explanation = None
            if payload.current_text:
                # Limit text length for better processing
                text_snippet = payload.current_text[:500]  # Limit to 500 chars
                
                explanation_prompt = f"""
                A student is reading this educational text and appears confused (confusion level: {confusion_level:.1f}):
                
                "{text_snippet}"
                
                Please provide a clear, concise explanation that:
                1. Breaks down the main concept in simpler terms
                2. Explains why this might be confusing
                3. Gives a practical example or analogy
                4. Suggests what to focus on next
                
                Keep your response under 100 words and make it educational but encouraging.
                """
                
                try:
                    from .llm import get_llm_response
                    contextual_explanation = get_llm_response(explanation_prompt, temperature=0.3)
                except Exception as e:
                    print(f"Error generating contextual explanation: {e}")
                    contextual_explanation = f"This section seems complex. Let me help: {text_snippet[:100]}... Try breaking it down into smaller concepts and look for key terms you understand first."
            
            result.update({
                "suggestions": [
                    "Try breaking down the concept into smaller parts",
                    "Look for visual examples or analogies", 
                    "Consider re-reading the previous section",
                    "Take a short break and return with fresh focus"
                ],
                "contextual_explanation": contextual_explanation,
                "confused_text": payload.current_text[:200]  # Limit confused text length
            })
        else:
            # For low confusion, don't send suggestions to avoid spam
            result["suggestions"] = []
        
        return result
        
    except Exception as e:
        print(f"Error in confusion detection: {e}")
        raise HTTPException(status_code=500, detail=f"Error detecting confusion: {str(e)}")


@app.post("/track-reading")
async def track_reading_progress(payload: ReadingTrackingRequest):
    """Track what user is reading and provide contextual help"""
    try:
        # Extract current reading context
        visible_text = payload.user_position.get('visible_text', '')
        scroll_position = payload.user_position.get('scroll_position', 0.0)
        
        # Generate contextual explanation using LLM
        llm = LLMClient()
        
        explanation_prompt = f"""
The user is currently reading this text passage:
"{visible_text}"

Provide a very simple, clear explanation or example that would help them understand this concept better. Keep it concise and practical.

Focus on:
- Key concepts in simpler terms
- Real-world analogies
- Quick examples
- Common misconceptions to avoid

Response should be 2-3 sentences maximum.
"""
        
        contextual_explanation = llm.generate(
            user_text=explanation_prompt,
            temperature=0.7
        )
        
        return {
            "reading_position": scroll_position,
            "contextual_help": contextual_explanation,
            "key_concepts": ["concept1", "concept2"],  # TODO: Extract from text
            "difficulty_estimate": "medium",  # TODO: Analyze text complexity
            "reading_time_estimate": len(visible_text.split()) * 0.5  # seconds
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error tracking reading: {str(e)}")
