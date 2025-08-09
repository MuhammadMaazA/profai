#!/usr/bin/env python3
"""
Text-to-Voice Test - Simple test without Gemini dependency for now
"""
import os
import sys
from pathlib import Path

# Ensure src is on path
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

def test_text_to_voice_simple():
    """Test text-to-voice with a simple hardcoded response"""
    print("🎙️  Testing Text-to-Voice (Simple)...")
    print("=" * 40)
    
    try:
        from profai.tts import TTSClient
        
        # Initialize TTS client
        tts = TTSClient()
        
        # Use a predefined response instead of generating one
        sample_responses = [
            "Hello! I'm ProfAI, your AI tutor. I'm here to help you learn about any topic you're curious about.",
            "Artificial Intelligence is a field of computer science that focuses on creating machines that can think and learn like humans.",
            "Machine learning is a subset of AI that enables computers to learn and improve from experience without being explicitly programmed for every task."
        ]
        
        print("Choose a sample response to convert to speech:")
        for i, response in enumerate(sample_responses, 1):
            print(f"{i}. {response[:50]}...")
        
        choice = input("Enter your choice (1-3) or press Enter for option 1: ").strip()
        
        try:
            idx = int(choice) - 1 if choice else 0
            if idx < 0 or idx >= len(sample_responses):
                idx = 0
        except ValueError:
            idx = 0
        
        selected_text = sample_responses[idx]
        print(f"🗣️  Selected text: {selected_text}")
        
        # Convert to speech
        print("🔊 Converting to speech...")
        audio_path = tts.synthesize(selected_text, play_audio=True)
        print(f"✅ Audio generated and played!")
        print(f"💾 Audio saved to: {audio_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Text-to-voice test failed: {e}")
        return False

def test_custom_text_to_voice():
    """Allow user to input custom text for TTS"""
    print("🎙️  Testing Custom Text-to-Voice...")
    print("=" * 40)
    
    try:
        from profai.tts import TTSClient
        
        # Initialize TTS client
        tts = TTSClient()
        
        # Get custom text from user
        custom_text = input("Enter text to convert to speech: ").strip()
        if not custom_text:
            custom_text = "This is a test of the text to speech functionality using ElevenLabs API."
        
        print(f"🗣️  Converting: {custom_text}")
        
        # Convert to speech
        print("🔊 Generating speech...")
        audio_path = tts.synthesize(custom_text, play_audio=True)
        print(f"✅ Audio generated and played!")
        print(f"💾 Audio saved to: {audio_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Custom text-to-voice test failed: {e}")
        return False

def check_tts_config():
    """Check TTS configuration"""
    print("🔍 Checking TTS Configuration...")
    print("=" * 40)
    
    try:
        from profai.config import settings
        
        if settings.elevenlabs_api_key and settings.elevenlabs_api_key.startswith("sk_"):
            print(f"✅ ElevenLabs API Key: {settings.elevenlabs_api_key[:15]}...")
        else:
            print("❌ ElevenLabs API Key not configured properly")
            return False
        
        print(f"✅ Voice: {settings.elevenlabs_voice}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration check failed: {e}")
        return False

def main():
    print("🎤 ProfAI Text-to-Voice Test")
    print("=" * 40)
    
    # Check configuration
    if not check_tts_config():
        print("\n❌ Please configure your ElevenLabs API key in .env file")
        return
    
    # Run tests
    while True:
        print("\n📋 Choose a test:")
        print("1. Sample Text-to-Voice")
        print("2. Custom Text-to-Voice")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            test_text_to_voice_simple()
        elif choice == "2":
            test_custom_text_to_voice()
        elif choice == "3":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice, please try again")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()
