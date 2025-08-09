# ProfAI

Emotionally intelligent AI tutor. This repo contains a minimal Phase 1 backend that lets you:

- Ask a question (CLI or API)
- Get an empathetic, concise answer from an LLM
- Hear the answer via ElevenLabs TTS

## Quickstart

1) Create and activate a virtual environment (Windows PowerShell):

```
python -m venv .venv; .\.venv\Scripts\Activate.ps1
```

2) Install dependencies:

```
pip install -r requirements.txt
```

3) Configure environment:

```
copy .env.example .env
# Edit .env and fill OPENAI_API_KEY and ELEVENLABS_API_KEY
```

4) Run the CLI for a text ➜ LLM ➜ speech round-trip (no keys needed in fake mode):

```
$env:PROFAI_DEV_FAKE='1'; $env:PYTHONPATH="src"; python -m profai.cli "What is photosynthesis?" --emotion neutral
```

5) Or run the API server:

```
$env:PROFAI_DEV_FAKE='1'; uvicorn profai.server:app --app-dir src --reload
```

Then POST to /ask with JSON like:

```
{
	"text": "Explain Newton's second law simply",
	"emotion": "confused",
	"play_audio": false
}
```

Audio files are saved under `outputs/`.

## Notes
- This is the Phase 1 foundation. SER (emotion from voice) and streaming are slated for Phase 2.
- Set ELEVENLABS_VOICE to any available voice name or ID. Default is `Bella`.
 - Dev mode: set `PROFAI_DEV_FAKE=1` to bypass external APIs. Use `scripts/smoke_test.py` to verify a full loop without keys.
 - STT: Use `/stt` with `{ "file_path": "path/to/audio.wav" }` in fake mode now; real transcription requires a valid `OPENAI_API_KEY`.
 - Microphone (prototype): run `scripts/mic_chat.py` to record 5s audio and then type your question; we’ll wire mic→STT next.
