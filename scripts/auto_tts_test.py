#!/usr/bin/env python3
"""
Automated TTS Test - Non-interactive test for text-to-speech
"""
import os
import sys
from pathlib import Path

# Ensure src is on path
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

def main():
    print("🎤 ProfAI Automated TTS Test")
    print("=" * 40)
    
    try:
        from profai.config import settings
        from profai.tts import TTSClient
        
        # Check configuration
        print("🔍 Checking configuration...")
        if not settings.elevenlabs_api_key or not settings.elevenlabs_api_key.startswith("sk_"):
            print("❌ ElevenLabs API key not configured")
            return
        
        print(f"✅ ElevenLabs API Key: {settings.elevenlabs_api_key[:15]}...")
        print(f"✅ Voice: {settings.elevenlabs_voice}")
        
        # Initialize TTS
        print("\n🔊 Initializing TTS client...")
        tts = TTSClient()
        
        # Test with sample text
        test_text = "Hello! This is ProfAI testing the text to speech functionality. If you can hear this, the integration is working perfectly!"
        
        print(f"🗣️  Testing with: {test_text}")
        print("🎵 Generating audio... (this may take a few seconds)")
        
        # Generate audio (don't play automatically to avoid blocking)
        audio_path = tts.synthesize(test_text, play_audio=False)
        
        print(f"✅ SUCCESS! Audio generated successfully!")
        print(f"💾 Audio file saved to: {audio_path}")
        print(f"🎧 You can play the audio file to test the voice quality.")
        
        # Check if file exists and get size
        if audio_path.exists():
            size = audio_path.stat().st_size
            print(f"📊 File size: {size} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Text-to-Speech test completed successfully!")
        print("🎯 Next step: Test voice-to-voice functionality")
    else:
        print("\n❌ Text-to-Speech test failed. Check your API configuration.")
