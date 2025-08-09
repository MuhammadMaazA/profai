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

4) Run the CLI for a text ➜ LLM ➜ speech round-trip:

```
python -m src.profai.cli "What is photosynthesis?" --emotion neutral
```

5) Or run the API server:

```
uvicorn src.profai.server:app --reload
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
