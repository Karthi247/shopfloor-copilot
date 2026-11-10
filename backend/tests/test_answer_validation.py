from app.services.answer_validation import has_lexical_support


def test_relevance_needs_a_lexical_anchor():
    assert has_lexical_support(
        "Where are rejected materials stored?",
        ["Rejected materials are placed in Quarantine Cage Q1."],
    )
    assert not has_lexical_support(
        "What should the machine operator do?",
        ["The machine operator controls the process."],
    )
    assert not has_lexical_support(
        "What is the outer diameter tolerance for BH-220?",
        [
            "The BH-220 bearing housing has a dimension out of tolerance on a characteristic marked Major."
        ],
    )
    assert has_lexical_support(
        "What is the outer diameter tolerance for BH-220?",
        ["BH-220 outer diameter 90.000 +/- 0.050 mm."],
    )
    assert not has_lexical_support(
        "How often should spindle runout be checked?",
        ["Spindle overload. Check tool wear and cutting parameters."],
    )
    assert has_lexical_support(
        "How often should spindle runout be checked?", ["Monthly check spindle runout."]
    )
    assert not has_lexical_support(
        "What does alarm AL-104 mean?",
        ["AL-101 Hydraulic pressure low. Operator action: stop cycle."],
    )
    assert not has_lexical_support(
        "For lot size 501 to 3,200, how many samples?",
        ["The sampling plan depends on lot size."],
    )
    assert has_lexical_support(
        "For lot size 501 to 3,200, how many samples?",
        ["Lot size: 501 - 3,200: inspect 32 samples."],
    )
    assert not has_lexical_support(
        "Where are rejected incoming materials stored?",
        ["Rejected lots are assessed by QC."],
    )
    assert has_lexical_support(
        "Where are rejected incoming materials stored?",
        ["Rejected material moved to Quarantine Cage Q1."],
    )
    assert not has_lexical_support(
        "What is the motor horsepower?",
        ["Incoming material inspection records lot number."],
    )
    assert not has_lexical_support("lockout steps", [])
