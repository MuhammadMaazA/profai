# ProfAI 🎓

An emotionally intelligent AI tutor with voice chat and YouTube-based curricula. ProfAI combines advanced AI conversation with interactive learning features including:

- **Voice Chat**: Real-time voice conversations with emotion detection
- **YouTube Curricula**: Process YouTube playlists into structured learning paths
- **Smart Reading Assistant**: Get instant explanations for confusing text
- **Personalized Quizzes**: AI-generated quizzes based on video content
- **Code Playground**: Interactive coding environment for learning
- **Confusion Detection**: Real-time help when you're struggling

## 🚀 Quick Start (Easiest Method)

### For Windows Users
1. **Double-click** `start_fullstack.bat` - This will automatically:
   - Install frontend dependencies
   - Start the backend server on port 8000
   - Start the frontend on port 3000
   - Open your browser to the application

### For All Platforms
1. **Run the Python launcher**:
   ```bash
   python start_fullstack.py
   ```

Both methods will automatically handle dependencies and start both servers. Your browser should open to `http://localhost:3000`.

## 📋 Manual Installation & Setup

### Prerequisites
- **Python 3.8+** - [Download from python.org](https://www.python.org/downloads/)
- **Node.js 16+** - [Download from nodejs.org](https://nodejs.org/)
- **Git** - [Download from git-scm.com](https://git-scm.com/)

### Step 1: Clone and Setup Backend

```bash
# Clone the repository
git clone <repository-url>
cd profai

# Create and activate virtual environment
# On Windows:
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# On macOS/Linux:
python -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment (Optional)

Create a `.env` file in the root directory for API keys:

```bash
# Copy example (if exists) or create new .env file
# Windows:
copy .env.example .env

# macOS/Linux:
cp .env.example .env
```

Edit `.env` and add your API keys:
```env
OPENAI_API_KEY=your_openai_key_here
ELEVENLABS_API_KEY=your_elevenlabs_key_here
ELEVENLABS_VOICE=Bella
```

**Note:** API keys are optional for development. The app runs in "fake mode" by default for testing without external API costs.

### Step 3: Setup Frontend

```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Return to root directory
cd ..
```

## 🏃‍♂️ Running the Application

### Method 1: Full Stack Launcher (Recommended)

```bash
# From the root directory:
python start_fullstack.py
```

This starts both servers and opens your browser automatically.

### Method 2: Manual Server Start

**Terminal 1 - Backend Server:**
```bash
# Set environment and start FastAPI server
set PYTHONPATH=src              # Windows
export PYTHONPATH=src           # macOS/Linux

uvicorn profai.server:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend Server:**
```bash
cd frontend
npm start
```

### Method 3: Command Line Interface Only

For backend-only usage:
```bash
# Set environment
set PROFAI_DEV_FAKE=1           # Windows
export PROFAI_DEV_FAKE=1        # macOS/Linux

set PYTHONPATH=src              # Windows  
export PYTHONPATH=src           # macOS/Linux

# Ask a question via CLI
python -m profai.cli "What is machine learning?" --emotion neutral
```

## 🌐 Accessing the Application

Once running, you can access:

- **🖥️ Frontend UI**: http://localhost:3000
- **📊 Backend API**: http://localhost:8000
- **📝 API Documentation**: http://localhost:8000/docs

## 🎯 Features Guide

### Voice Chat
- Click the microphone button to start recording
- Speak your question and click again to stop
- ProfAI responds with both text and audio

### YouTube Curricula
1. Switch to the "YouTube Curricula" tab
2. Enter a YouTube playlist URL
3. The system will process videos into chapters
4. Read transcripts, take quizzes, and track progress

### Smart Reading Assistant
- Select any confusing text to get instant explanations
- Get simplified explanations and context

### Code Playground
- Interactive coding environment
- Test code snippets while learning

## 🛠️ Development Mode

For development without API costs, the app runs in "fake mode" by default:

```bash
# Explicitly enable fake mode
set PROFAI_DEV_FAKE=1           # Windows
export PROFAI_DEV_FAKE=1        # macOS/Linux
```

This simulates API responses without making actual calls to OpenAI or ElevenLabs.

## 📁 Project Structure

```
profai/
├── frontend/                   # React frontend application
│   ├── src/
│   │   ├── App.js             # Main app component
│   │   ├── components/        # Reusable components
│   │   └── *.js               # Feature components
│   └── package.json
├── src/profai/                # Python backend
│   ├── server.py              # FastAPI server
│   ├── cli.py                 # Command line interface
│   ├── llm.py                 # LLM integration
│   ├── tts.py                 # Text-to-speech
│   ├── stt.py                 # Speech-to-text
│   └── *.py                   # Other modules
├── scripts/                   # Utility scripts
├── start_fullstack.py         # Full stack launcher
├── start_fullstack.bat        # Windows batch launcher
└── requirements.txt           # Python dependencies
```

## 🧪 Testing

Test the installation:

```bash
# Test CLI functionality
python scripts/smoke_test.py

# Test voice pipeline
python scripts/voice_pipeline_test.py

# Test individual components
python scripts/quick_test.py
```

## ❓ Troubleshooting

### Common Issues

**"Node.js not found"**
- Install Node.js from [nodejs.org](https://nodejs.org/)
- Restart your terminal after installation

**"Python module not found"**
- Ensure virtual environment is activated
- Check that `PYTHONPATH=src` is set

**"Port already in use"**
- Stop existing servers: `Ctrl+C` in terminals
- Or change ports in the configuration

**Frontend won't start**
- Try deleting `frontend/node_modules` and run `npm install` again
- Check Node.js version: `node --version` (needs 16+)

**API calls failing**
- Check if backend is running on port 8000
- Verify `.env` file configuration for production mode

### Getting Help

1. Check the [troubleshooting scripts](scripts/) for automated testing
2. Review the API docs at http://localhost:8000/docs when server is running
3. Check console logs in browser developer tools

## 🔧 Configuration Options

### Environment Variables

- `PROFAI_DEV_FAKE`: Set to '1' for development mode (no API calls)
- `OPENAI_API_KEY`: Your OpenAI API key for GPT models
- `ELEVENLABS_API_KEY`: Your ElevenLabs API key for voice synthesis
- `ELEVENLABS_VOICE`: Voice name/ID for TTS (default: "Bella")

### Audio Settings

Audio files are automatically saved to the `outputs/` directory.

## 📝 Notes

- **Development Phase**: This is a Phase 1 implementation focused on core functionality
- **API Costs**: Use fake mode for development to avoid API charges
- **Voice Features**: Real-time emotion detection and streaming planned for Phase 2
- **Browser Compatibility**: Tested on Chrome, Firefox, Safari, and Edge
