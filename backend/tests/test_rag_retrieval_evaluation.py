import json
import logging

import pytest

from app.config import settings
from app.services import answer_service
from app.services.answer_validation import select_supported_hits
from app.services.retrieval_service import Retriever

CASES = [
    (
        "What is the recommended coolant concentration for the TX-200 CNC turning centre?",
        "MNT-MAN-CNC-02_TX-200_Preventive_Maintenance.pdf",
        "6 - 8 %",
    ),
    (
        "The machine is showing alarm AL-104. What does it mean and what should the operator do?",
        "MNT-MAN-CNC-02_TX-200_Preventive_Maintenance.pdf",
        "ISO VG 68",
    ),
    (
        "Who is allowed to remove a lockout lock from a machine?",
        "SAF-SOP-003_Lockout_Tagout_Procedure.pdf",
        "Production Manager",
    ),
    (
        "What is the outer diameter tolerance for the BH-220 bearing housing?",
        "QC-SOP-014_Rev04_Incoming_Material_Inspection.pdf",
        "90.000",
    ),
    (
        "How often should spindle runout be checked, and who does it?",
        "MNT-MAN-CNC-02_TX-200_Preventive_Maintenance.pdf",
        "Maintenance technician",
    ),
    (
        "What should the inspection team do if a supplier does not provide the Material Test Certificate (MTC)?",
        "QC-SOP-014_Rev04_Incoming_Material_Inspection.pdf",
        "MTC is mandatory",
    ),
    (
        "How many samples should be inspected for a lot size of 600 under QC-SOP-014 Rev 04?",
        "QC-SOP-014_Rev04_Incoming_Material_Inspection.pdf",
        "Samples to inspect: 32",
    ),
    (
        "What should happen if an authorized employee leaves the workplace without removing their LOTO lock?",
        "SAF-SOP-003_Lockout_Tagout_Procedure.pdf",
        "SF-12 Lock Removal Record",
    ),
    (
        "what is coolant percentage for tx200?",
        "MNT-MAN-CNC-02_TX-200_Preventive_Maintenance.pdf",
        "6 - 8 %",
    ),
    (
        "AL104 alarm coming what should i do?",
        "MNT-MAN-CNC-02_TX-200_Preventive_Maintenance.pdf",
        "ISO VG 68",
    ),
    (
        "tell me BH220 outer diameter tolerance.",
        "QC-SOP-014_Rev04_Incoming_Material_Inspection.pdf",
        "90.000",
    ),
    (
        "when spindle runout check need to do?",
        "MNT-MAN-CNC-02_TX-200_Preventive_Maintenance.pdf",
        "Frequency: Monthly",
    ),
    (
        "for 600 lot size how many sample required?",
        "QC-SOP-014_Rev04_Incoming_Material_Inspection.pdf",
        "Samples to inspect: 32",
    ),
    (
        "who can remove another employee LOTO lock?",
        "SAF-SOP-003_Lockout_Tagout_Procedure.pdf",
        "Production Manager",
    ),
]


@pytest.fixture(scope="module")
def indexed_retriever():
    try:
        retriever = Retriever()
    except (RuntimeError, OSError) as exc:
        pytest.skip(f"Local embedding model is unavailable: {exc}")
    if retriever.collection.count() == 0:
        pytest.skip("No local Chroma index is available for retrieval evaluation")
    return retriever


@pytest.mark.parametrize("question, expected_filename, evidence", CASES)
def test_live_retrieval_finds_expected_source_and_evidence(
    indexed_retriever, question, expected_filename, evidence
):
    candidates = indexed_retriever.search(question)
    supported = select_supported_hits(
        question, candidates, settings.similarity_threshold, settings.top_k
    )

    expected_hits = [hit for hit in supported if hit["filename"] == expected_filename]
    assert expected_hits, f"Expected source {expected_filename} for {question!r}"
    normalized_evidence = " ".join(evidence.casefold().split())
    normalized_text = " ".join(
        " ".join(hit["text"] for hit in expected_hits).casefold().split()
    )
    assert normalized_evidence in normalized_text


def test_live_retrieval_refuses_unanswerable_electricity_question(indexed_retriever):
    question = "What is the annual electricity consumption of the manufacturing plant?"
    candidates = indexed_retriever.search(question)
    supported = select_supported_hits(
        question, candidates, settings.similarity_threshold, settings.top_k
    )
    assert not supported


def test_loto_follow_up_retrieval_keeps_record_and_next_shift_notice(indexed_retriever):
    question = (
        "What should happen if an authorized employee leaves the workplace "
        "without removing their LOTO lock?"
    )
    hits = select_supported_hits(
        question,
        indexed_retriever.search(question),
        settings.similarity_threshold,
        settings.top_k,
    )
    context = " ".join(hit["text"] for hit in hits).casefold()
    assert "sf-12 lock removal record" in context
    assert "lock owner must be informed" in context


def test_explicit_historical_revision_is_not_mixed_with_current_revision(
    indexed_retriever,
):
    question = "How many samples does QC-SOP-014 Rev 03 require for 600 parts?"
    hits = select_supported_hits(
        question,
        indexed_retriever.search(question, revision_question=question),
        settings.similarity_threshold,
        settings.top_k,
    )
    assert hits
    assert {hit["revision"] for hit in hits} == {3}
    assert "draw 5 samples" in " ".join(hit["text"] for hit in hits).casefold()


def test_answer_service_builds_complete_loto_context_without_calling_groq(monkeypatch):
    question = (
        "What should happen if an authorized employee leaves the workplace "
        "without removing their LOTO lock?"
    )
    source_name = "SAF-SOP-003_Lockout_Tagout_Procedure.pdf"
    excerpts = [
        {
            "text": (
                "Authorized employees must follow LOTO lock removal. If the lock owner "
                "is absent, the Shift Supervisor attempts to contact the owner. If "
                "unreachable, the Production Manager and Safety Officer must both "
                "authorize removing the lock."
            ),
            "distance": 0.3,
            "document_number": "SAF-SOP-003",
            "revision": 5,
            "revision_known": True,
            "filename": source_name,
            "page": 1,
            "title": "Lockout Tagout Procedure",
            "effective_date": "12-Feb-2026",
            "section_heading": "Lock Removal",
        },
        {
            "text": (
                "Removal is recorded on form SF-12 Lock Removal Record. The lock owner "
                "must be informed before they resume work on their next shift."
            ),
            "distance": 0.35,
            "document_number": "SAF-SOP-003",
            "revision": 5,
            "revision_known": True,
            "filename": source_name,
            "page": 2,
            "title": "Lockout Tagout Procedure",
            "effective_date": "12-Feb-2026",
            "section_heading": "Lock Removal",
        },
    ]

    class FakeRetriever:
        def search(self, *_args, **_kwargs):
            return excerpts

    class ContextCapture:
        context = ""

        def generate(self, question, context, history):
            self.context = context
            return "The procedure requires the recorded removal and lock-owner notice."

    provider = ContextCapture()
    monkeypatch.setattr(answer_service, "Retriever", FakeRetriever)
    monkeypatch.setattr(answer_service, "get_provider", lambda: provider)
    answer = answer_service.answer_question(question)
    assert answer["answered"]
    assert "SF-12 Lock Removal Record" in provider.context
    assert "lock owner must be informed before they resume work" in provider.context


def test_debug_retrieval_event_is_structured(indexed_retriever, monkeypatch, caplog):
    monkeypatch.setattr(settings, "rag_debug", True)
    with caplog.at_level(logging.INFO, logger="app.services.retrieval_service"):
        indexed_retriever.search("What is the coolant concentration for TX-200?")
    lines = [
        record.getMessage().split("RAG_DIAGNOSTIC ", 1)[1]
        for record in caplog.records
        if "RAG_DIAGNOSTIC " in record.getMessage()
    ]
    assert lines
    event = json.loads(lines[-1])
    assert event["event"] == "retrieval_complete"
    assert event["embedding_model"] == settings.embedding_model
    assert event["collection"] == "shopfloor_documents"
    assert event["candidates"]
