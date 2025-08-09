#!/usr/bin/env python3
"""
Simple test for Gemini API integration
"""
import os
import sys
from pathlib import Path

# Ensure src is on path
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

def test_gemini():
    print("🧪 Testing Gemini API Integration...")
    
    try:
        from profai.config import settings
        from profai.llm import LLMClient
        
        print(f"✅ Gemini API Key configured: {'Yes' if settings.gemini_api_key else 'No'}")
        print(f"✅ Using Gemini: {settings.use_gemini}")
        print(f"✅ Model: {settings.model}")
        
        # Test LLM
        llm = LLMClient()
        print("🤔 Testing Gemini response...")
        
        response = llm.generate("Say hello and explain what you are in one sentence.", emotion="friendly")
        print(f"🤖 Gemini Response: {response}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_tts():
    print("\n🔊 Testing Text-to-Speech...")
    
    try:
        from profai.tts import TTSClient
        
        tts = TTSClient()
        print("🎵 Testing TTS with sample text...")
        
        # Test with a short message
        test_text = "Hello! This is a test of the text to speech functionality."
        audio_path = tts.synthesize(test_text, play_audio=False)
        print(f"✅ Audio generated: {audio_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ TTS test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 ProfAI Quick Test")
    print("=" * 30)
    
    success = True
    success &= test_gemini()
    success &= test_tts()
    
    if success:
        print("\n🎉 All tests passed! Ready for voice chat.")
    else:
        print("\n❌ Some tests failed. Check your API keys in .env file.")
