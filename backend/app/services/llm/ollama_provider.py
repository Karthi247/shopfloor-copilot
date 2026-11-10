import httpx

from app.config import settings
from app.services.llm.base import LLMProvider
from app.services.llm.groq_provider import SYSTEM


class OllamaProvider(LLMProvider):
    def generate(
        self, question: str, context: str, history: list[dict[str, str]] | None = None
    ) -> str:
        try:
            messages = [{"role": "system", "content": SYSTEM}]
            messages.extend(
                {"role": turn["role"], "content": turn["content"]}
                for turn in (history or [])[-8:]
            )
            messages.append(
                {
                    "role": "user",
                    "content": f"Retrieved excerpts:\n{context}\n\nLatest question: {question}",
                }
            )
            response = httpx.post(
                f"{settings.ollama_base_url.rstrip('/')}/api/chat",
                timeout=45,
                json={
                    "model": settings.ollama_model,
                    "stream": False,
                    "messages": messages,
                },
            )
            response.raise_for_status()
            return response.json()["message"]["content"]
        except httpx.HTTPError as exc:
            raise RuntimeError(
                "Could not reach Ollama. Check that the local service is running and the model is available."
            ) from exc
