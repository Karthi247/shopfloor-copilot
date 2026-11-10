import re
from functools import lru_cache

import chromadb
from sentence_transformers import SentenceTransformer

from app.config import settings
from app.services.answer_validation import lexical_match_count
from app.services.revision_service import latest_revision, select_revisions


@lru_cache(maxsize=1)
def _embedding_model():
    try:
        return SentenceTransformer(settings.embedding_model, local_files_only=True)
    except OSError as exc:
        raise RuntimeError(
            "The embedding model is not cached locally. Run the document ingestion command once while model downloads are available."
        ) from exc


class Retriever:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=str(settings.chroma_path))
        self.collection = self.client.get_or_create_collection(
            "shopfloor_documents", metadata={"hnsw:space": "cosine"}
        )
        self.model = _embedding_model()

    def search(
        self, question: str, k: int | None = None, revision_question: str | None = None
    ):
        if self.collection.count() == 0:
            return []
        revision_question = revision_question or question
        vec = self.model.encode([question], normalize_embeddings=True).tolist()
        metadata = self.collection.get(include=["metadatas"])["metadatas"]
        requested_revisions = {
            int(match.group(1))
            for match in re.finditer(
                r"\b(?:rev(?:ision)?\s*)0?(\d+)\b", revision_question, re.I
            )
        }
        by_document = {}
        for item in metadata:
            if item.get("revision_known"):
                by_document.setdefault(item["document_number"], []).append(item)
        allowed = set()
        for item in metadata:
            number, revision = item["document_number"], item["revision"]
            if requested_revisions:
                if item.get("revision_known") and revision in requested_revisions:
                    allowed.add((number, revision))
            elif not item.get("revision_known") or revision == latest_revision(
                by_document.get(number, [])
            ):
                allowed.add((number, revision))
        clauses = [
            {"$and": [{"document_number": number}, {"revision": revision}]}
            for number, revision in sorted(allowed)
        ]
        if not clauses:
            return []
        where = clauses[0] if len(clauses) == 1 else {"$or": clauses}
        result = self.collection.query(
            query_embeddings=vec,
            n_results=min(max((k or settings.top_k) * 5, 25), self.collection.count()),
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        hits = [
            {"text": d, **m, "distance": float(dist)}
            for d, m, dist in zip(
                result["documents"][0], result["metadatas"][0], result["distances"][0]
            )
        ]
        hits = select_revisions(hits, revision_question)
        hits.sort(
            key=lambda hit: (
                -lexical_match_count(question, hit["text"]),
                hit["distance"],
            )
        )
        return hits[: (k or settings.top_k)]
