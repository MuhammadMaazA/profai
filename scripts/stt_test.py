#!/usr/bin/env python3
"""
Speech-to-Text Test - Test voice recognition functionality
"""
import os
import sys
from pathlib import Path

# Ensure src is on path
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

def test_stt_with_existing_files():
    """Test STT with existing voice input files"""
    print("🎤 Testing Speech-to-Text with existing files...")
    print("=" * 50)
    
    try:
        from profai.config import settings
        from profai.stt import STTClient
        
        # Check OpenAI API key for STT
        if not settings.openai_api_key or settings.openai_api_key == "your_openai_api_key_here":
            print("❌ OpenAI API key not configured for Speech-to-Text")
            print("💡 STT requires OpenAI API key for Whisper transcription")
            print("🔧 Please add OPENAI_API_KEY to your .env file")
            return False
        
        print(f"✅ OpenAI API Key configured: {settings.openai_api_key[:15]}...")
        
        # Initialize STT client
        stt = STTClient()
        
        # Find existing voice input files
        outputs_dir = Path("outputs")
        voice_files = list(outputs_dir.glob("voice_input_*.wav"))
        
        if not voice_files:
            print("❌ No voice input files found in outputs directory")
            return False
        
        # Test with the most recent voice file
        test_file = sorted(voice_files)[-1]
        print(f"🎵 Testing with file: {test_file}")
        
        # Transcribe the audio
        print("📝 Transcribing audio...")
        transcription = stt.transcribe_file(str(test_file))
        
        print(f"✅ Transcription result: '{transcription}'")
        
        if transcription.strip():
            print("🎉 Speech-to-Text test successful!")
            return True
        else:
            print("⚠️  Empty transcription - file might be silent or corrupted")
            return False
            
    except Exception as e:
        print(f"❌ STT test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fake_stt():
    """Test STT in fake mode (no API calls)"""
    print("🎤 Testing Speech-to-Text in fake mode...")
    print("=" * 50)
    
    try:
        # Enable fake mode
        os.environ["PROFAI_DEV_FAKE"] = "1"
        
        from profai.stt import STTClient
        
        # Initialize STT client in fake mode
        stt = STTClient()
        
        # Test with any file (won't actually process in fake mode)
        fake_file = "dummy_file.wav"
        
        print("📝 Testing transcription in fake mode...")
        transcription = stt.transcribe_file(fake_file)
        
        print(f"✅ Fake transcription: '{transcription}'")
        
        if "[FAKE TRANSCRIPT]" in transcription:
            print("🎉 Fake STT test successful!")
            return True
        else:
            print("❌ Fake mode not working properly")
            return False
            
    except Exception as e:
        print(f"❌ Fake STT test failed: {e}")
        return False
    finally:
        # Disable fake mode
        if "PROFAI_DEV_FAKE" in os.environ:
            del os.environ["PROFAI_DEV_FAKE"]

def main():
    print("🎤 ProfAI Speech-to-Text Test")
    print("=" * 40)
    
    # Test fake mode first (always works)
    success_fake = test_fake_stt()
    
    # Test real STT if possible
    success_real = test_stt_with_existing_files()
    
    if success_fake and success_real:
        print("\n🎉 Both STT tests passed!")
        print("✅ Ready for voice-to-voice functionality")
        return True
    elif success_fake:
        print("\n⚠️  Fake STT works, but real STT needs OpenAI API key")
        print("🔧 Add OPENAI_API_KEY to .env file for full functionality")
        return False
    else:
        print("\n❌ STT tests failed")
        return False

if __name__ == "__main__":
    main()
