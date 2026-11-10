import math
import re
from difflib import get_close_matches

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "been",
    "being",
    "by",
    "can",
    "could",
    "did",
    "do",
    "does",
    "for",
    "from",
    "had",
    "has",
    "have",
    "how",
    "i",
    "in",
    "into",
    "is",
    "it",
    "me",
    "my",
    "of",
    "on",
    "or",
    "our",
    "should",
    "the",
    "their",
    "them",
    "there",
    "these",
    "this",
    "those",
    "to",
    "under",
    "was",
    "we",
    "were",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "will",
    "with",
    "would",
    "you",
    "your",
    "please",
    "tell",
    "show",
    "explain",
    "mean",
    "happen",
    "happens",
    "thing",
    "things",
    "machine",
    "machines",
    "procedure",
    "procedures",
    "material",
    "materials",
    "question",
    "operator",
    "current",
    "many",
    "often",
    "check",
    "checking",
    "checked",
    "need",
    "needs",
    "needed",
    "require",
    "required",
}

CONCEPT_GROUPS = (
    {"percentage", "percent", "concentration", "proportion", "ratio"},
    {"quantity", "amount", "number", "count", "sample", "sampling"},
    {"frequency", "often", "monthly", "weekly", "daily", "annually"},
    {"check", "checking", "checked", "inspect", "inspection", "inspecting"},
    {"remove", "removal", "removed", "takeoff", "take", "off"},
    {"person", "people", "employee", "employees", "owner", "operator"},
    {"stored", "store", "kept", "placed", "move", "moved", "relocated"},
)
_CONCEPT_FORMS = {word: group for group in CONCEPT_GROUPS for word in group}
_TOKEN = re.compile(
    r"[A-Za-z]{2,}\d+[A-Za-z0-9-]*|[A-Za-z]+(?:-[A-Za-z0-9]+)*|"
    r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?"
)
_IDENTIFIER = re.compile(r"(?=.*[A-Za-z])(?=.*\d)[A-Za-z0-9-]+\Z")


def _tokens(text: str) -> list[str]:
    return _TOKEN.findall(text)


def _compact_identifier(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def _stem(word: str) -> set[str]:
    forms = {word}
    if len(word) > 5 and word.endswith("ies"):
        forms.add(word[:-3] + "y")
    if len(word) > 5 and word.endswith("ing"):
        forms.add(word[:-3])
        forms.add(word[:-3] + "e")
    if len(word) > 4 and word.endswith("ed"):
        forms.add(word[:-2])
        forms.add(word[:-1])
    if len(word) > 4 and word.endswith("es"):
        forms.add(word[:-2])
    elif len(word) > 3 and word.endswith("s"):
        forms.add(word[:-1])
    return forms


def _is_identifier(token: str) -> bool:
    return bool(_IDENTIFIER.fullmatch(token))


def _anchors(question: str) -> list[str]:
    return [
        token.casefold()
        for token in _tokens(question)
        if token.casefold() not in STOPWORDS
    ]


def _number_supported(token: str, passage: str) -> bool:
    try:
        number = float(token.replace(",", ""))
    except ValueError:
        return False
    normalized = passage.replace(",", "")
    if re.search(rf"(?<!\d){re.escape(token)}(?!\d)", normalized, re.I):
        return True
    ranges = re.finditer(
        r"(?<!\w)(\d+(?:\.\d+)?)\s*(?:to|[-–])\s*(\d+(?:\.\d+)?)(?!\w)",
        normalized,
        re.I,
    )
    return any(
        float(match.group(1)) <= number <= float(match.group(2)) for match in ranges
    )


def _token_supported(token: str, passage: str, passage_tokens: set[str]) -> bool:
    if _is_identifier(token):
        return _compact_identifier(token) in {
            _compact_identifier(item) for item in passage_tokens
        }
    if token.isdigit() or re.fullmatch(r"\d+\.\d+", token):
        return _number_supported(token, passage)

    forms = _stem(token)
    concept = _CONCEPT_FORMS.get(token)
    if concept:
        forms |= concept
    if any(form in passage_tokens for form in forms):
        return True

    # Fuzzy matching is limited to ordinary words; identifiers and numbers stay exact.
    if len(token) >= 5:
        return bool(get_close_matches(token, passage_tokens, n=1, cutoff=0.82))
    return False


def lexical_match_count(question: str, passage: str) -> int:
    anchors = _anchors(question)
    passage_tokens = {token.casefold() for token in _tokens(passage)}
    return sum(
        _token_supported(token, passage.casefold(), passage_tokens) for token in anchors
    )


def has_lexical_support(question: str, passages: list[str]) -> bool:
    if not passages:
        return False
    passage = " ".join(passages)
    anchors = _anchors(question)
    if not anchors:
        return False

    # If a numeric range is stated, both endpoints must be present in the evidence.
    numeric_range = re.search(
        r"(?<!\w)(\d[\d,]*(?:\.\d+)?)\s*(?:to|[-–])\s*(\d[\d,]*(?:\.\d+)?)(?!\w)",
        question,
        re.I,
    )
    if numeric_range:
        numbers = passage.replace(",", "")
        if any(
            value.replace(",", "") not in numbers for value in numeric_range.groups()
        ):
            return False

    passage_tokens = {token.casefold() for token in _tokens(passage)}
    matches = {
        token
        for token in anchors
        if _token_supported(token, passage.casefold(), passage_tokens)
    }
    identifiers = {token for token in anchors if _is_identifier(token)}
    if identifiers and not identifiers.issubset(matches):
        return False

    non_identifiers = [token for token in anchors if token not in identifiers]
    if identifiers:
        required = min(
            len(non_identifiers), max(1, math.ceil(len(non_identifiers) * 0.5))
        )
    else:
        required = min(
            len(non_identifiers), max(2, math.ceil(len(non_identifiers) * 0.6))
        )
    return len(matches - identifiers) >= required


def select_supported_hits(
    question: str, candidates: list[dict], threshold: float, limit: int
):
    """Apply the distance and lexical evidence gates, including split evidence."""
    within_distance = [hit for hit in candidates if hit["distance"] <= threshold]
    selected = [
        hit for hit in within_distance if has_lexical_support(question, [hit["text"]])
    ]
    selected_keys = {
        (hit.get("filename"), hit.get("page"), hit.get("revision")) for hit in selected
    }

    groups = {}
    for hit in within_distance:
        document_number = hit.get("document_number")
        group_key = (
            document_number,
            hit.get("revision"),
            hit.get("filename") if document_number in (None, "UNKNOWN") else None,
        )
        groups.setdefault(group_key, []).append(hit)
    for group in groups.values():
        if not has_lexical_support(question, [hit["text"] for hit in group]):
            continue
        for hit in group:
            key = (hit.get("filename"), hit.get("page"), hit.get("revision"))
            if key not in selected_keys and lexical_match_count(question, hit["text"]):
                selected.append(hit)
                selected_keys.add(key)

    selected.sort(
        key=lambda hit: (
            -lexical_match_count(question, hit["text"]),
            hit["distance"],
            hit.get("filename", ""),
            hit.get("page", 0),
        )
    )
    return selected[:limit]
