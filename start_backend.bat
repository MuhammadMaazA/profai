@echo off
echo 🚀 Starting ProfAI Backend Server
echo =================================

cd /d "%~dp0"

echo 📦 Installing Python packages...
pip install fastapi uvicorn[standard] python-multipart python-dotenv openai elevenlabs google-generativeai sounddevice soundfile

echo 🔧 Setting environment...
set PYTHONPATH=src

echo 🌐 Starting FastAPI server on http://localhost:8000...
python -m uvicorn profai.server:app --reload --host 127.0.0.1 --port 8000

pause
