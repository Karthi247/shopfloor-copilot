from app.services.query_normalization import normalize_identifiers, safe_log_text


def test_identifier_rewriting_uses_only_identifiers_found_in_passages():
    passages = ["Alarm AL-104 is low. TX-200 coolant is 6 - 8 percent."]
    assert normalize_identifiers("AL104 for tx 200", passages) == "AL-104 for TX-200"
    assert normalize_identifiers("BH220", passages) == "BH220"


def test_debug_log_redacts_common_secret_assignments_and_phrases():
    message = (
        'api_key="gsk-private" and password is hunter2; Authorization: Bearer abc123'
    )
    safe = safe_log_text(message)
    assert "gsk-private" not in safe
    assert "hunter2" not in safe
    assert "abc123" not in safe
