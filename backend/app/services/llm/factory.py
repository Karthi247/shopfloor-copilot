from app.config import settings
from app.services.llm.groq_provider import GroqProvider
from app.services.llm.ollama_provider import OllamaProvider


def get_provider():
    if settings.provider == "groq":
        return GroqProvider()
    if settings.provider == "ollama":
        return OllamaProvider()
    raise RuntimeError("LLM_PROVIDER must be either 'groq' or 'ollama'.")
