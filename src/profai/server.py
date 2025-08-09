from __future__ import annotations
from typing import Optional, List
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


class AskRequest(BaseModel):
    text: str
    emotion: Optional[str] = None
    play_audio: bool = False
    learning_path: Optional[str] = None
    delivery_format: Optional[str] = None
    lesson_id: Optional[str] = None
    conversation_history: Optional[List[str]] = None


class STTRequest(BaseModel):
    file_path: str


class LessonRequest(BaseModel):
    lesson_id: str
    learning_path: str
    delivery_format: str
    user_question: Optional[str] = None


class ProgressRequest(BaseModel):
    conversation_history: List[str]
    current_lesson: Optional[str] = None


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/curriculum")
async def get_curriculum():
    """Get the full curriculum structure"""
    return {
        "lessons": {
            lesson_id: {
                "title": lesson.title,
                "path": lesson.path.value,
                "format": lesson.format.value,
                "duration_minutes": lesson.duration_minutes,
                "difficulty": lesson.difficulty,
                "prerequisites": lesson.prerequisites,
                "learning_objectives": lesson.learning_objectives
            }
            for lesson_id, lesson in ALL_LESSONS.items()
        },
        "learning_paths": [path.value for path in LearningPath],
        "delivery_formats": [format.value for format in DeliveryFormat]
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
        
        print(f"TTS endpoint: generating with emotion '{user_emotion}' for text length {len(payload.text)}")
        path = tts.synthesize(payload.text, voice=payload.voice, play_audio=payload.play_audio, user_emotion=user_emotion)
        return {"audio_path": str(path)}
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
            conversation_history=payload.conversation_history
        )
        
        # Generate TTS with emotion-aware voice settings
        print(f"Generating TTS for text request with detected emotion: {user_emotion}")
        path = tts.synthesize(answer, play_audio=payload.play_audio, user_emotion=user_emotion)
        return {"answer": answer, "audio_path": str(path)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/voice-chat")
async def voice_chat_endpoint(audio_file: UploadFile = File(...)):
    """Complete voice-to-voice chat endpoint with emotional intelligence"""
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
        
        # Step 2: Analyze emotion and generate AI response with educational focus
        emotion_analysis = emotion_detector.analyze_text_emotion(transcription)
        
        response = llm.generate(
            user_text=transcription, 
            emotion=emotion_analysis.primary_emotion.value,
            learning_path=LearningPath.HYBRID,  # Default to hybrid learning
            delivery_format=DeliveryFormat.AUDIO_LESSONS  # Optimized for audio
        )
        
        # Step 3: Convert response to speech with emotion-based voice settings
        print(f"Generating TTS for response length: {len(response)} characters, user emotion: {emotion_analysis.primary_emotion.value}")
        audio_path = tts.synthesize(response, play_audio=False, user_emotion=emotion_analysis.primary_emotion.value)
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
