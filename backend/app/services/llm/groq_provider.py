from groq import Groq

from app.config import settings
from app.services.llm.base import LLMProvider

SYSTEM = """You are ShopFloor AI Copilot, an assistant for manufacturing supervisors. Answer using only supplied retrieved company document excerpts. Do not use external knowledge. Never invent safety instructions, machine parameters, inspection tolerances, maintenance schedules, approval responsibilities, or technical specifications. Do not add facts by inference, including negative claims such as 'the older revision has no such distinction.' Preserve job titles exactly as written; do not broaden a named role to a department or team. When asked who performs a task, use the complete role title from the excerpt, including qualifiers such as technician, engineer, or supervisor. Do not add a synonym or equipment detail unless it is supported by an excerpt. If the excerpts do not answer the question, say exactly: 'I could not find this information in the available documents. Please consult the relevant department or authorized supervisor.' Prefer concise clear English and numbered steps. Preserve values and units accurately. Do not write document citations or page numbers in the answer body; the application attaches verified source cards from indexed metadata. Never invent a page number. For current questions, use the latest applicable revision. If a user explicitly asks for a historical revision or comparison, use the requested revision(s), keep each revision's instructions separate, and explain which revision each statement comes from. Conversation history may help resolve references in the latest question, but it is not evidence; only retrieved excerpts support factual claims. Answer only the latest question. Before responding, check that every claim and title is directly supported by an excerpt. Never treat assumptions as official procedure."""


class GroqProvider(LLMProvider):
    def __init__(self):
        if not settings.groq_api_key:
            raise RuntimeError(
                "Groq is selected but GROQ_API_KEY is not configured. Add it to backend/.env."
            )
        self.client = Groq(api_key=settings.groq_api_key, timeout=25, max_retries=1)

    def generate(
        self, question: str, context: str, history: list[dict[str, str]] | None = None
    ) -> str:
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
        response = self.client.chat.completions.create(
            model=settings.groq_model,
            temperature=0,
            messages=messages,
        )
        return response.choices[0].message.content or ""
