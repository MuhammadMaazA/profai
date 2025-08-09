from __future__ import annotations
from typing import Optional
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
from .prof_ai import ProfAIEducationClient


app = FastAPI(title="ProfAI API", version="0.1.0")

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


class AskRequest(BaseModel):
    text: str
    emotion: Optional[str] = None
    play_audio: bool = False
    user_id: Optional[str] = "default_user"


class StartModuleRequest(BaseModel):
    user_id: str
    module_id: str


class ProgressRequest(BaseModel):
    user_id: str


class STTRequest(BaseModel):
    file_path: str



@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/tts")
async def tts_endpoint(payload: TTSRequest):
    try:
        tts = TTSClient()
        path = tts.synthesize(payload.text, voice=payload.voice, play_audio=payload.play_audio)
        return {"audio_path": path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ask")
async def ask_endpoint(payload: AskRequest):
    try:
        # Use enhanced ProfAI for educational responses
        prof_ai = ProfAIEducationClient()
        result = prof_ai.generate_educational_response(
            user_text=payload.text,
            user_id=payload.user_id or "default_user"
        )
        
        # Generate audio if requested
        audio_filename = None
        if payload.play_audio:
            tts = TTSClient()
            path = tts.synthesize(result["response"], play_audio=False)
            audio_filename = path.name if hasattr(path, 'name') else Path(path).name
        
        return {
            "answer": result["response"],
            "audio_path": audio_filename,
            "educational_context": {
                "detected_emotion": result["detected_emotion"],
                "confidence_level": result["confidence_level"],
                "current_module": result["current_module"],
                "suggested_action": result["suggested_next_action"]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/stt")
async def stt_endpoint(payload: STTRequest):
    try:
        stt = STTClient()
        text = stt.transcribe_file(payload.file_path)
        return {"text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/voice-chat")
async def voice_chat_endpoint(audio_file: UploadFile = File(...)):
    """Complete voice-to-voice chat endpoint"""
    try:
        # Save uploaded audio file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            content = await audio_file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
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
        # Save uploaded file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
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


@app.post("/start-module")
async def start_module_endpoint(payload: StartModuleRequest):
    """Start a new learning module"""
    try:
        prof_ai = ProfAIEducationClient()
        result = prof_ai.start_module(payload.user_id, payload.module_id)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/progress/{user_id}")
async def get_progress_endpoint(user_id: str):
    """Get learning progress for a user"""
    try:
        prof_ai = ProfAIEducationClient()
        progress = prof_ai.get_learning_progress(user_id)
        return progress
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/curriculum")
async def get_curriculum_endpoint():
    """Get available curriculum modules"""
    try:
        prof_ai = ProfAIEducationClient()
        curriculum = prof_ai.curriculum_manager.modules
        
        # Format for frontend consumption
        formatted_curriculum = {}
        for module_id, module_info in curriculum.items():
            formatted_curriculum[module_id] = {
                "id": module_id,
                "title": module_info["title"],
                "description": module_info["description"],
                "difficulty": module_info["difficulty"],
                "estimated_time": module_info["estimated_time"],
                "prerequisites": module_info.get("prerequisites", []),
                "theory_count": len(module_info.get("theory_topics", [])),
                "project_count": len(module_info.get("hands_on_projects", []))
            }
        
        return {"modules": formatted_curriculum}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/voice-chat-enhanced")
async def voice_chat_enhanced_endpoint(audio_file: UploadFile = File(...), user_id: str = "default_user"):
    """Enhanced voice-to-voice chat with educational intelligence"""
    try:
        # Save uploaded audio file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            content = await audio_file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Initialize clients
        stt = STTClient()
        prof_ai = ProfAIEducationClient()
        tts = TTSClient()
        
        # Step 1: Transcribe audio
        transcription = stt.transcribe_file(tmp_file_path)
        
        # Clean up temp file
        os.unlink(tmp_file_path)
        
        if not transcription.strip():
            raise HTTPException(status_code=400, detail="No speech detected in audio")
        
        # Step 2: Generate educational response
        educational_result = prof_ai.generate_educational_response(
            user_text=transcription,
            user_id=user_id
        )
        
        # Step 3: Convert response to speech
        audio_path = tts.synthesize(educational_result["response"], play_audio=False)
        audio_url = f"/audio/{audio_path.name}"
        
        return {
            "transcription": transcription,
            "response": educational_result["response"],
            "audio_url": audio_url,
            "educational_context": {
                "detected_emotion": educational_result["detected_emotion"],
                "confidence_level": educational_result["confidence_level"],
                "current_module": educational_result["current_module"],
                "suggested_action": educational_result["suggested_next_action"]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
