from __future__ import annotations
import argparse

from .llm import LLMClient
from .tts import TTSClient


def main() -> None:
    parser = argparse.ArgumentParser(description="ProfAI CLI: ask a question and hear the answer.")
    parser.add_argument("question", nargs="?", help="Your question (if omitted, you'll be prompted)")
    parser.add_argument("--emotion", default="neutral", help="Emotion hint: neutral|frustrated|confused|enthusiastic")
    parser.add_argument("--no-play", action="store_true", help="Do not play audio, only save to file")
    args = parser.parse_args()

    q = args.question or input("Ask ProfAI: ")

    llm = LLMClient()
    tts = TTSClient()

    answer = llm.generate(q, emotion=args.emotion)
    print("\nProfAI:", answer)
    out_path = tts.synthesize(answer, play_audio=not args.no_play)
    print(f"\nAudio saved to: {out_path}")


if __name__ == "__main__":
    main()
