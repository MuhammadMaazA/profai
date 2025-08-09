from __future__ import annotations
import os

# Force fake mode so no real API calls are made
os.environ.setdefault("PROFAI_DEV_FAKE", "1")

from src.profai.llm import LLMClient
from src.profai.tts import TTSClient


def main():
    llm = LLMClient(api_key=None)
    tts = TTSClient(api_key=None)
    answer = llm.generate("What is photosynthesis?", emotion="neutral")
    print("Answer:", answer)
    path = tts.synthesize(answer, play_audio=False)
    print("Audio at:", path)


if __name__ == "__main__":
    main()
