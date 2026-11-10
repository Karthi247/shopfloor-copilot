import re

_IDENTIFIER = re.compile(r"\b[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+\b|\b[A-Z]{2,}\d{2,}\b", re.I)
_SECRET = re.compile(
    r"(?i)([\"']?(?:api[_ -]?key|password|passwd|secret|access[_ -]?token|bearer)"
    r"[\"']?\s*[:=]\s*[\"']?)[^\"'\s,;}]+"
)
_SECRET_PHRASE = re.compile(
    r"(?i)(\b(?:api[_ -]?key|password|passwd|secret|access[_ -]?token|bearer)"
    r"\s+(?:is\s+)?)[^\s,;]+"
)


def _compact(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def known_identifiers(passages: list[str]) -> list[str]:
    found = {
        match.group(0).upper()
        for text in passages
        for match in _IDENTIFIER.finditer(text)
    }
    return sorted(found, key=len, reverse=True)


def normalize_identifiers(question: str, passages: list[str]) -> str:
    """Apply only identifier spellings evidenced by retrieved documents."""
    normalized = question
    for identifier in known_identifiers(passages):
        compact = _compact(identifier)
        pattern = re.compile(
            r"(?<![A-Za-z0-9])"
            + r"[\s-]*".join(map(re.escape, compact))
            + r"(?![A-Za-z0-9])",
            re.I,
        )
        normalized = pattern.sub(identifier, normalized)
    return normalized


def safe_log_text(text: str, limit: int = 320) -> str:
    redacted = _SECRET.sub(r"\1[REDACTED]", text)
    redacted = _SECRET_PHRASE.sub(r"\1[REDACTED]", redacted)
    return " ".join(redacted.split())[:limit]
