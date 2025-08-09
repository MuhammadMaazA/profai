from __future__ import annotations
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .llm import LLMClient
from .tts import TTSClient


app = FastAPI(title="ProfAI API", version="0.1.0")


class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = None
    play_audio: bool = False


class AskRequest(BaseModel):
    text: str
    emotion: Optional[str] = None
    play_audio: bool = False


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
