import logging
import re

from app.config import settings
from app.services.answer_validation import select_supported_hits
from app.services.llm.factory import get_provider
from app.services.query_normalization import safe_log_text
from app.services.rag_diagnostics import log_rag_event
from app.services.retrieval_service import Retriever

NO_ANSWER = "I could not find this information in the available documents. Please consult the relevant department or authorized supervisor."
logger = logging.getLogger(__name__)


def answer_question(question: str, history: list[dict[str, str]] | None = None):
    history = history or []
    previous_user_questions = [
        turn["content"]
        for turn in history
        if turn.get("role") == "user" and turn.get("content")
    ]
    retrieval_question = question
    has_follow_up_reference = bool(
        re.search(
            r"\b(?:it|that|this|those|them|there|same)\b|^\s*(?:what|how)\s+about\b",
            question,
            re.I,
        )
    )
    if has_follow_up_reference and previous_user_questions:
        retrieval_question = f"{previous_user_questions[-1]}\n{question}"
    retriever = Retriever()
    candidates = retriever.search(
        retrieval_question, k=settings.top_k, revision_question=question
    )
    hits = select_supported_hits(
        retrieval_question,
        candidates,
        threshold=settings.similarity_threshold,
        limit=settings.top_k,
    )

    if settings.rag_debug:
        accepted_keys = {
            (hit.get("filename"), hit.get("page"), hit.get("revision")) for hit in hits
        }
        decisions = []
        for hit in candidates:
            key = (hit.get("filename"), hit.get("page"), hit.get("revision"))
            if key in accepted_keys:
                reason = "accepted"
            elif hit["distance"] > settings.similarity_threshold:
                reason = "cosine_distance_above_threshold"
            else:
                reason = "insufficient_lexical_evidence"
            decisions.append(
                {
                    "filename": hit.get("filename"),
                    "revision": hit.get("revision"),
                    "page": hit.get("page"),
                    "distance": round(hit["distance"], 4),
                    "decision": reason,
                    "preview": safe_log_text(hit["text"], 180),
                }
            )
        log_rag_event(
            logger,
            "answer_gate",
            original_question=safe_log_text(question),
            candidate_count=len(candidates),
            accepted_count=len(hits),
            cosine_distance_threshold=settings.similarity_threshold,
            decisions=decisions[:50],
        )
    if not hits:
        if settings.rag_debug:
            log_rag_event(
                logger,
                "final_refusal",
                original_question=safe_log_text(question),
            )
        return {
            "answer": NO_ANSWER,
            "sources": [],
            "revision_note": None,
            "safety_critical": any(
                w in question.lower()
                for w in ("lockout", "tagout", "emergency", "safety")
            ),
            "answered": False,
        }
    context = "\n\n".join(
        f"[{h['document_number']} Rev {h['revision'] or 'unknown'}, {h['filename']}, page {h['page']}]\n{h['text']}"
        for h in hits
    )
    if settings.rag_debug:
        log_rag_event(
            logger,
            "context_sent_to_provider",
            context=safe_log_text(context, 1000000),
            source_count=len(hits),
        )
    text = get_provider().generate(question, context, history)
    if not text.strip() or NO_ANSWER.lower() in text.lower():
        if settings.rag_debug:
            log_rag_event(
                logger,
                "provider_no_answer",
                original_question=safe_log_text(question),
                sources=len(hits),
            )
        return {
            "answer": NO_ANSWER,
            "sources": [],
            "revision_note": None,
            "safety_critical": any(
                w in question.lower()
                for w in ("lockout", "tagout", "emergency", "safety", "hazard")
            ),
            "answered": False,
        }
    sources = [
        {
            "document_number": h["document_number"],
            "title": h["title"],
            "revision": h["revision"] or None,
            "effective_date": h.get("effective_date"),
            "filename": h["filename"],
            "page": h["page"],
            "section_heading": h.get("section_heading"),
        }
        for h in hits
    ]
    unique = {(s["document_number"], s["revision"]) for s in sources}
    note = None
    requested_revisions = sorted(
        {
            int(match.group(1))
            for match in re.finditer(r"\b(?:rev(?:ision)?\s*)0?(\d+)\b", question, re.I)
        }
    )
    if len(requested_revisions) > 1:
        note = (
            "Revision comparison requested: "
            + " and ".join(f"Rev {revision:02d}" for revision in requested_revisions)
            + ". Instructions are shown separately by revision."
        )
    elif requested_revisions:
        if any(revision != requested_revisions[0] for _number, revision in unique):
            note = "Revision metadata could not be confidently matched to the requested historical revision; verify the controlled source document."
        elif unique:
            note = f"Historical revision {requested_revisions[0]:02d} was explicitly requested."
    elif any(number == "QC-SOP-014" for number, _revision in unique):
        note = "Current procedure uses the latest effective indexed QC-SOP-014 revision. Older revisions remain searchable when named explicitly."
    if any(source["revision"] is None for source in sources):
        note = (
            (note + " " if note else "")
            + "Revision metadata could not be confidently identified for every cited source."
        )
    if any(
        not source["effective_date"] or source["effective_date"] == "Unknown"
        for source in sources
    ):
        note = (
            (note + " " if note else "")
            + "Effective-date metadata is incomplete; verify which revision is approved for use."
        )
    if settings.rag_debug:
        log_rag_event(
            logger,
            "final_answer",
            original_question=safe_log_text(question),
            source_count=len(sources),
            sources=[
                {
                    "document_number": source["document_number"],
                    "revision": source["revision"],
                    "filename": source["filename"],
                    "page": source["page"],
                }
                for source in sources
            ],
        )
    return {
        "answer": text or NO_ANSWER,
        "sources": sources,
        "revision_note": note,
        "safety_critical": any(
            w in question.lower()
            for w in ("lockout", "tagout", "emergency", "safety", "hazard")
        ),
        "answered": bool(text),
    }
