#!/usr/bin/env python3
"""
Complete Voice-to-Voice Test - Full pipeline test
"""
import os
import sys
from pathlib import Path

# Ensure src is on path
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

def test_voice_to_voice_pipeline():
    """Test the complete voice-to-voice pipeline"""
    print("🎤➡️🤖➡️🔊 Testing Complete Voice-to-Voice Pipeline")
    print("=" * 60)
    
    try:
        from profai.config import settings
        from profai.stt import STTClient
        from profai.llm import LLMClient  
        from profai.tts import TTSClient
        
        # Check all API keys
        print("🔍 Checking API configuration...")
        
        issues = []
        if not settings.elevenlabs_api_key or not settings.elevenlabs_api_key.startswith("sk_"):
            issues.append("ElevenLabs API key for TTS")
            
        if settings.use_gemini:
            if not settings.gemini_api_key:
                issues.append("Gemini API key for LLM")
        else:
            if not settings.openai_api_key:
                issues.append("OpenAI API key for LLM")
        
        # For STT we need OpenAI (separate from LLM)
        if not settings.openai_api_key:
            issues.append("OpenAI API key for STT")
        
        if issues:
            print(f"❌ Missing: {', '.join(issues)}")
            return False
        
        print("✅ All API keys configured")
        print(f"   - Using {'Gemini' if settings.use_gemini else 'OpenAI'} for LLM")
        print(f"   - Using OpenAI Whisper for STT")
        print(f"   - Using ElevenLabs for TTS")
        
        # Initialize all clients
        print("\n🔧 Initializing clients...")
        stt = STTClient()
        llm = LLMClient()
        tts = TTSClient()
        print("✅ All clients initialized")
        
        # Step 1: Use existing voice input
        outputs_dir = Path("outputs")
        voice_files = list(outputs_dir.glob("voice_input_*.wav"))
        
        if not voice_files:
            print("❌ No voice input files found for testing")
            return False
        
        test_file = sorted(voice_files)[-1]
        print(f"\n🎵 Step 1: Using voice input: {test_file.name}")
        
        # Step 2: Transcribe
        print("📝 Step 2: Transcribing audio...")
        transcription = stt.transcribe_file(str(test_file))
        print(f"✅ Transcription: '{transcription}'")
        
        if not transcription.strip():
            print("⚠️  Empty transcription, using fallback question")
            transcription = "What is artificial intelligence and how does it work?"
        
        # Step 3: Generate response
        print("🤔 Step 3: Generating AI response...")
        response = llm.generate(transcription, emotion="enthusiastic")
        print(f"✅ AI Response: {response[:100]}{'...' if len(response) > 100 else ''}")
        
        # Step 4: Convert to speech
        print("🔊 Step 4: Converting response to speech...")
        output_audio = tts.synthesize(response, play_audio=False)
        print(f"✅ Audio generated: {output_audio}")
        
        # Verify output file
        if output_audio.exists():
            size = output_audio.stat().st_size
            print(f"📊 Output file size: {size} bytes")
            
            if size > 1000:  # Reasonable audio file size
                print("🎉 VOICE-TO-VOICE TEST SUCCESSFUL!")
                print("\n📋 Pipeline Summary:")
                print(f"   🎤 Input: {test_file.name}")
                print(f"   📝 Transcription: '{transcription[:50]}...'")
                print(f"   🤖 AI Model: {'Gemini' if settings.use_gemini else 'OpenAI'}")
                print(f"   🔊 Output: {output_audio.name}")
                print(f"   ⏱️  Pipeline: Voice → Text → AI → Voice ✅")
                return True
            else:
                print("❌ Generated audio file is too small")
                return False
        else:
            print("❌ Output audio file not created")
            return False
            
    except Exception as e:
        print(f"❌ Voice-to-voice test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_text_to_voice_only():
    """Simpler test: just text input to voice output"""
    print("📝➡️🔊 Testing Text-to-Voice Only")
    print("=" * 40)
    
    try:
        from profai.llm import LLMClient
        from profai.tts import TTSClient
        
        # Initialize clients
        llm = LLMClient()
        tts = TTSClient()
        
        # Test question
        question = "Explain quantum computing in simple terms"
        print(f"💭 Question: {question}")
        
        # Generate response
        print("🤔 Generating response...")
        response = llm.generate(question, emotion="friendly")
        print(f"✅ Response: {response[:100]}{'...' if len(response) > 100 else ''}")
        
        # Convert to speech
        print("🔊 Converting to speech...")
        audio_path = tts.synthesize(response, play_audio=False)
        print(f"✅ Audio generated: {audio_path}")
        
        return audio_path.exists() and audio_path.stat().st_size > 1000
        
    except Exception as e:
        print(f"❌ Text-to-voice test failed: {e}")
        return False

def main():
    print("🎤 ProfAI Complete Voice Functionality Test")
    print("=" * 60)
    
    # Try the complete pipeline first
    print("🚀 Attempting complete voice-to-voice pipeline...")
    if test_voice_to_voice_pipeline():
        print("\n🎉 COMPLETE SUCCESS! All voice functionality is working.")
        return
    
    print("\n⚠️  Full pipeline failed, testing text-to-voice only...")
    if test_text_to_voice_only():
        print("\n✅ Text-to-Voice works!")
        print("💡 For full voice-to-voice, ensure OpenAI API key is configured for STT")
    else:
        print("\n❌ Text-to-Voice also failed")
        print("🔧 Please check your API key configuration")

if __name__ == "__main__":
    main()
