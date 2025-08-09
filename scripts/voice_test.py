#!/usr/bin/env python3
"""
Voice Chat Test - Test voice-to-voice and text-to-voice functionality with Gemini API
"""
import os
import sys
from pathlib import Path

# Ensure src is on path
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Import ProfAI components
from profai.llm import LLMClient
from profai.tts import TTSClient
from profai.stt import STTClient


def test_text_to_voice():
    """Test text-to-voice functionality"""
    print("🎙️  Testing Text-to-Voice...")
    print("=" * 40)
    
    try:
        # Initialize clients
        llm = LLMClient()
        tts = TTSClient()
        
        # Get user input
        user_text = input("Enter your question: ")
        if not user_text.strip():
            user_text = "What is artificial intelligence?"
        
        print(f"💭 Your question: {user_text}")
        print("🤔 Generating response with Gemini...")
        
        # Generate response
        response = llm.generate(user_text, emotion="friendly")
        print(f"✅ AI Response: {response}")
        
        # Convert to speech
        print("🔊 Converting to speech...")
        audio_path = tts.synthesize(response, play_audio=True)
        print(f"💾 Audio saved to: {audio_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Text-to-voice test failed: {e}")
        return False


def test_voice_to_voice():
    """Test complete voice-to-voice functionality"""
    print("\n🎤 Testing Voice-to-Voice...")
    print("=" * 40)
    
    try:
        # Initialize all clients
        stt = STTClient()
        llm = LLMClient()
        tts = TTSClient()
        
        print("🎙️  Recording audio... Speak now!")
        print("💡 You have 5 seconds to speak your question...")
        
        # Record audio (using mic_chat functionality)
        import queue
        import sounddevice as sd
        import soundfile as sf
        
        q = queue.Queue()
        
        def callback(indata, frames, time, status):  # noqa: ARG001
            q.put(indata.copy())
        
        # Create output directory
        outputs_dir = ROOT / "outputs"
        outputs_dir.mkdir(exist_ok=True)
        
        # Record audio
        filename = outputs_dir / "voice_input_test.wav"
        samplerate = 16000
        channels = 1
        seconds = 5.0
        
        with sf.SoundFile(str(filename), mode='w', samplerate=samplerate, channels=channels, subtype='PCM_16') as file:
            with sd.InputStream(samplerate=samplerate, channels=channels, callback=callback):
                sd.sleep(int(seconds * 1000))
                while not q.empty():
                    file.write(q.get())
        
        print(f"🎵 Audio recorded: {filename}")
        
        # Transcribe audio
        print("📝 Transcribing audio...")
        transcription = stt.transcribe_file(str(filename))
        print(f"💭 You said: {transcription}")
        
        if not transcription.strip():
            print("⚠️  No speech detected, using fallback question")
            transcription = "Tell me about machine learning"
        
        # Generate response
        print("🤔 Generating response with Gemini...")
        response = llm.generate(transcription, emotion="enthusiastic")
        print(f"✅ AI Response: {response}")
        
        # Convert to speech
        print("🔊 Converting to speech...")
        audio_path = tts.synthesize(response, play_audio=True)
        print(f"💾 Response audio saved to: {audio_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Voice-to-voice test failed: {e}")
        return False


def check_api_keys():
    """Check if API keys are properly configured"""
    print("🔍 Checking API Configuration...")
    print("=" * 40)
    
    from profai.config import settings
    
    # Check Gemini API key
    if settings.gemini_api_key and settings.gemini_api_key != "your_gemini_api_key_here":
        print(f"✅ Gemini API Key: {settings.gemini_api_key[:20]}...")
    else:
        print("❌ Gemini API Key not configured")
        return False
    
    # Check ElevenLabs API key
    if settings.elevenlabs_api_key and settings.elevenlabs_api_key != "your_elevenlabs_api_key_here":
        print(f"✅ ElevenLabs API Key: {settings.elevenlabs_api_key[:20]}...")
    else:
        print("❌ ElevenLabs API Key not configured")
        return False
    
    print(f"✅ Model: {settings.model}")
    print(f"✅ Voice: {settings.elevenlabs_voice}")
    print(f"✅ Using Gemini: {settings.use_gemini}")
    
    return True


def main():
    print("🎤 ProfAI Voice Chat Test Suite")
    print("=" * 50)
    
    # Check API keys first
    if not check_api_keys():
        print("\n❌ Please configure your API keys in .env file")
        print("💡 Set GEMINI_API_KEY and ELEVENLABS_API_KEY")
        return
    
    # Run tests
    while True:
        print("\n📋 Choose a test:")
        print("1. Text-to-Voice Test")
        print("2. Voice-to-Voice Test") 
        print("3. Run Both Tests")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            test_text_to_voice()
        elif choice == "2":
            test_voice_to_voice()
        elif choice == "3":
            print("🚀 Running all tests...")
            test_text_to_voice()
            test_voice_to_voice()
        elif choice == "4":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice, please try again")
        
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
