import re

from app.config import settings
from app.services.answer_validation import has_lexical_support
from app.services.llm.factory import get_provider
from app.services.retrieval_service import Retriever

NO_ANSWER = "I could not find this information in the available documents. Please consult the relevant department or authorized supervisor."


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
    hits = retriever.search(retrieval_question, revision_question=question)
    # Similarity is a gate, not evidence by itself: require a lexical anchor as well.
    hits = [
        h
        for h in hits
        if h["distance"] <= settings.similarity_threshold
        and has_lexical_support(retrieval_question, [h["text"]])
    ]
    if not hits:
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
    text = get_provider().generate(question, context, history)
    if not text.strip() or NO_ANSWER.lower() in text.lower():
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
