from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @abstractmethod
    def generate(
        self, question: str, context: str, history: list[dict[str, str]] | None = None
    ) -> str: ...
