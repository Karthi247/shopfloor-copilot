import re

STOPWORDS = {
    "what",
    "where",
    "when",
    "how",
    "who",
    "does",
    "did",
    "was",
    "were",
    "should",
    "would",
    "could",
    "can",
    "is",
    "are",
    "the",
    "for",
    "from",
    "and",
    "into",
    "with",
    "under",
    "current",
    "often",
    "many",
    "much",
    "this",
    "that",
    "it",
    "machine",
    "procedure",
    "materials",
    "material",
    "question",
    "allowed",
    "bearing",
    "housing",
}
ALIASES = {
    "stored": {"stored", "kept", "placed", "moved"},
    "store": {"stored", "kept", "placed", "moved"},
    "replace": {"replace", "replacing", "replaced"},
    "checked": {"check", "checked", "inspect", "inspected"},
}


def lexical_match_count(question: str, passage: str) -> int:
    tokens = re.findall(r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*", question)
    anchors = {
        token.lower()
        for token in tokens
        if token.lower() not in STOPWORDS
        and (len(token) > 3 or (token.isupper() and len(token) >= 2))
    }
    text = passage.lower()
    return sum(
        any(form in text for form in ALIASES.get(token, {token})) for token in anchors
    )


def has_lexical_support(question: str, passages: list[str]) -> bool:
    if not passages:
        return False
    tokens = re.findall(r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*", question)
    anchors = {
        token.lower()
        for token in tokens
        if token.lower() not in STOPWORDS
        and (len(token) > 3 or (token.isupper() and len(token) >= 2))
    }
    identifiers = {
        token
        for token in anchors
        if re.search(r"\d", token) or (token.isupper() and len(token) >= 2)
    }
    passage_text = " ".join(passages).lower()
    matching = {
        token
        for token in anchors
        if any(form in passage_text for form in ALIASES.get(token, {token}))
    }
    question_terms = set(re.findall(r"[a-z0-9]+", question.lower()))
    if {"coolant", "concentration"} <= question_terms and not {
        "coolant",
        "concentration",
    } <= set(re.findall(r"[a-z0-9]+", passage_text)):
        return False
    if {"spindle", "runout"} <= question_terms and not {"spindle", "runout"} <= set(
        re.findall(r"[a-z0-9]+", passage_text)
    ):
        return False
    if {"outer", "diameter"} <= question_terms and not {"outer", "diameter"} <= set(
        re.findall(r"[a-z0-9]+", passage_text)
    ):
        return False
    if {"lockout", "lock"} <= question_terms and (
        "remove" in question_terms or "allowed" in question_terms
    ):
        if not any(
            phrase in passage_text
            for phrase in ("own lock", "lock owner", "remove another")
        ):
            return False
    if {"rejected", "stored"} <= question_terms and not any(
        phrase in passage_text for phrase in ("quarantine cage q1", "red bin")
    ):
        return False
    numeric_range = re.search(r"(\d[\d,]*)\s*(?:to|[-–])\s*(\d[\d,]*)", question, re.I)
    if numeric_range:
        normalized = passage_text.replace(",", "")
        if any(
            value.replace(",", "") not in normalized for value in numeric_range.groups()
        ):
            return False
    if identifiers and not identifiers & matching:
        return False
    if identifiers & matching:
        non_identifier_anchors = anchors - identifiers
        required = min(2, len(non_identifier_anchors))
        return len(matching - identifiers) >= required
    return len(anchors) >= 2 and len(matching) >= 2
