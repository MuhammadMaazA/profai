from __future__ import annotations
import os
import sys
import queue
from pathlib import Path
import sounddevice as sd
import soundfile as sf

# Ensure src on path
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Fake mode toggle optional
os.environ.setdefault("PROFAI_DEV_FAKE", "1")

from profai.llm import LLMClient
from profai.tts import TTSClient


def record_microphone(seconds: float = 5.0, samplerate: int = 16000, channels: int = 1) -> Path:
    q = queue.Queue()

    def callback(indata, frames, time, status):  # noqa: ARG001
        q.put(indata.copy())

    filename = ROOT / "outputs" / "mic_input.wav"
    filename.parent.mkdir(parents=True, exist_ok=True)

    with sf.SoundFile(str(filename), mode='w', samplerate=samplerate, channels=channels, subtype='PCM_16') as file:
        with sd.InputStream(samplerate=samplerate, channels=channels, callback=callback):
            sd.sleep(int(seconds * 1000))
            while not q.empty():
                file.write(q.get())
    return filename


def main():
    print("Recording 5 seconds... Speak now")
    wav = record_microphone(seconds=5.0)
    print(f"Saved: {wav}")

    # In Phase 2 we'd transcribe wav via STT. For now, prompt via input for clarity.
    text = input("Type your question (mic transcription coming next phase): ")

    llm = LLMClient()
    tts = TTSClient()
    answer = llm.generate(text, emotion="neutral")
    print("Answer:", answer)
    path = tts.synthesize(answer, play_audio=True)
    print("Audio at:", path)


if __name__ == "__main__":
    main()
