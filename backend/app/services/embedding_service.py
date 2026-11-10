from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.config import settings


@lru_cache(maxsize=1)
def load_embedding_model():
    try:
        return SentenceTransformer(settings.embedding_model, local_files_only=True)
    except OSError as exc:
        raise RuntimeError(
            "The embedding model is not cached locally. Run ingestion once while model downloads are available."
        ) from exc
