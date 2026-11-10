from app.services.revision_service import latest_revision, select_revisions


def test_revision_selection_keeps_history():
    hits = [
        {
            "document_number": "QC-SOP-014",
            "revision": 3,
            "revision_known": True,
            "distance": 0.1,
            "text": "paper form",
        },
        {
            "document_number": "QC-SOP-014",
            "revision": 4,
            "revision_known": True,
            "distance": 0.2,
            "text": "digital form",
        },
    ]
    selected = select_revisions(hits, "What is the current form?")
    assert [h["revision"] for h in selected] == [4]
    historical = select_revisions(hits, "What form did Rev 03 use?")
    assert [h["revision"] for h in historical] == [3]
    comparison = select_revisions(hits, "Compare Rev 03 and Rev 04 forms")
    assert [h["revision"] for h in comparison] == [3, 4]


def test_latest_effective_revision_wins_over_larger_revision_number():
    rows = [
        {"revision": 3, "revision_known": True, "effective_date": "01-Jul-2026"},
        {"revision": 4, "revision_known": True, "effective_date": "01-Jan-2026"},
    ]
    assert latest_revision(rows) == 3
