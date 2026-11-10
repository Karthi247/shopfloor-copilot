import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
load_dotenv(ROOT / "backend" / ".env")


class Settings:
    provider = os.getenv("LLM_PROVIDER", "groq").lower()
    groq_api_key = os.getenv("GROQ_API_KEY", "")
    groq_model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3.1")
    embedding_model = os.getenv(
        "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )
    chroma_path = ROOT / os.getenv("CHROMA_PATH", "backend/data/chroma_db")
    documents_path = ROOT / os.getenv("DOCUMENTS_PATH", "data/Documents")
    top_k = int(os.getenv("TOP_K", "5"))
    similarity_threshold = float(os.getenv("SIMILARITY_THRESHOLD", "0.95"))
    admin_token = os.getenv("ADMIN_TOKEN", "")
    auth_secret_key = os.getenv("AUTH_SECRET_KEY", "")
    cors_origins = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
        ).split(",")
        if origin.strip()
    ]
    auth_database_path = ROOT / os.getenv(
        "AUTH_DATABASE_PATH", "backend/data/users.sqlite3"
    )


settings = Settings()
