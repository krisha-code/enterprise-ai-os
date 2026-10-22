import os

import httpx


class LLMService:

    OLLAMA_URL = os.getenv(
        "OLLAMA_URL",
        "http://localhost:11434/api/generate",
    )
    MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")

    @staticmethod
    async def generate(prompt: str) -> str:
        payload = {
            "model": LLMService.MODEL,
            "prompt": prompt,
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                LLMService.OLLAMA_URL,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        return data["response"]