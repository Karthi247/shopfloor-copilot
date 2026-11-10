import logging
import re

import chromadb

from app.config import settings
from app.services.answer_validation import lexical_match_count
from app.services.embedding_service import load_embedding_model
from app.services.query_normalization import normalize_identifiers, safe_log_text
from app.services.rag_diagnostics import log_rag_event
from app.services.revision_service import latest_revision, select_revisions

logger = logging.getLogger(__name__)


class Retriever:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=str(settings.chroma_path))
        self.collection = self.client.get_or_create_collection(
            "shopfloor_documents", metadata={"hnsw:space": "cosine"}
        )
        self.model = load_embedding_model()

    def _revision_filter(self, revision_question: str):
        metadata = self.collection.get(include=["metadatas"])["metadatas"]
        requested = {
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
            if requested:
                if item.get("revision_known") and revision in requested:
                    allowed.add((number, revision))
            elif not item.get("revision_known") or revision == latest_revision(
                by_document.get(number, [])
            ):
                allowed.add((number, revision))

        clauses = [
            {"$and": [{"document_number": number}, {"revision": revision}]}
            for number, revision in sorted(allowed)
        ]
        filter_details = {
            "metadata_records": len(metadata),
            "eligible_document_revisions": sorted(allowed),
            "eligible_chunk_records": sum(
                (item["document_number"], item["revision"]) in allowed
                for item in metadata
            ),
            "requested_revisions": sorted(requested),
            "mode": "explicit revision" if requested else "latest effective revision",
        }
        if not clauses:
            return None, filter_details
        where = clauses[0] if len(clauses) == 1 else {"$or": clauses}
        return where, filter_details

    def search(
        self, question: str, k: int | None = None, revision_question: str | None = None
    ):
        total_count = self.collection.count()
        if total_count == 0:
            if settings.rag_debug:
                log_rag_event(
                    logger,
                    "retrieval_empty_index",
                    question=safe_log_text(question),
                )
            return []

        revision_question = revision_question or question
        where, filter_details = self._revision_filter(revision_question)
        if where is None:
            if settings.rag_debug:
                log_rag_event(
                    logger,
                    "revision_filter_empty",
                    question=safe_log_text(question),
                    revision_filter=filter_details,
                )
            return []

        candidate_count = min(max((k or settings.top_k) * 5, 25), total_count)

        def query(text: str):
            vector = self.model.encode([text], normalize_embeddings=True).tolist()
            return self.collection.query(
                query_embeddings=vector,
                n_results=candidate_count,
                where=where,
                include=["documents", "metadatas", "distances"],
            )

        first = query(question)
        known_passages = first["documents"][0]
        normalized_query = normalize_identifiers(question, known_passages)
        results = [first]
        if normalized_query.casefold() != question.casefold():
            results.append(query(normalized_query))

        candidates = {}
        debug_candidates = []
        for result in results:
            for ident, document, metadata, distance in zip(
                result["ids"][0],
                result["documents"][0],
                result["metadatas"][0],
                result["distances"][0],
            ):
                score = float(distance)
                old = candidates.get(ident)
                if old is None or score < old["distance"]:
                    candidates[ident] = {
                        "text": document,
                        **metadata,
                        "distance": score,
                    }
                if settings.rag_debug:
                    debug_candidates.append(
                        {
                            "filename": metadata.get("filename"),
                            "revision": metadata.get("revision"),
                            "page": metadata.get("page"),
                            "distance": round(score, 4),
                            "preview": safe_log_text(document),
                        }
                    )

        hits = select_revisions(list(candidates.values()), revision_question)
        hits.sort(
            key=lambda hit: (
                -lexical_match_count(normalized_query, hit["text"]),
                hit["distance"],
                hit.get("filename", ""),
                hit.get("page", 0),
            )
        )

        if settings.rag_debug:
            log_rag_event(
                logger,
                "retrieval_complete",
                original_question=safe_log_text(question),
                normalized_question=safe_log_text(normalized_query),
                embedding_model=settings.embedding_model,
                collection=self.collection.name,
                indexed_chunks=total_count,
                revision_filter=filter_details,
                candidate_count=len(candidates),
                after_revision_filter=len(hits),
                cosine_distance_threshold=settings.similarity_threshold,
                candidates=debug_candidates[: min(len(debug_candidates), 50)],
            )
        return hits
