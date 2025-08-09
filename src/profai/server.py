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
        llm = LLMClient()
        tts = TTSClient()
        answer = llm.generate(payload.text, emotion=payload.emotion)
        path = tts.synthesize(answer, play_audio=payload.play_audio)
        return {"answer": answer, "audio_path": path}
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
