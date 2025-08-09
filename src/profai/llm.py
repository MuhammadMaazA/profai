from __future__ import annotations
from typing import Optional

from openai import OpenAI

from .config import settings
from .prompts import build_system_prompt


class LLMClient:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None) -> None:
        self.api_key = api_key or settings.openai_api_key
        if not self.api_key:
            raise RuntimeError(
                "OPENAI_API_KEY not set. Please set environment variable OPENAI_API_KEY."
            )
        self.model = model or settings.model
        self.client = OpenAI(api_key=self.api_key)

    def generate(self, user_text: str, emotion: Optional[str] = None, temperature: float = 0.7) -> str:
        system_prompt = build_system_prompt(emotion)
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
            ],
            temperature=temperature,
        )
        return resp.choices[0].message.content or ""
