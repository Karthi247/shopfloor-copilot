import re

CHUNKING_VERSION = "line-aware-v2"

_HEADING = re.compile(r"^\s*(?:\d+(?:\.\d+)*[.)]?\s+|[A-Z][A-Z0-9 /&()_-]{3,}:?\s*$)")
_SECTION_HEADING = re.compile(r"^\s*\d+(?:\.\d+)*[.)]?\s+[A-Z][^.!?]{2,100}$")
_TABLE_ROW = re.compile(r"\||\t|\s{2,}")


def _units(text: str) -> list[str]:
    """Keep headings, paragraphs and table rows intact as far as possible."""
    lines = [line.strip() for line in text.splitlines()]
    units: list[str] = []
    current: list[str] = []

    def flush():
        if current:
            units.append(" ".join(current))
            current.clear()

    for line in lines:
        if not line:
            flush()
            continue
        # A table row or heading is an atomic unit, even when it follows prose.
        if _TABLE_ROW.search(line) or _HEADING.match(line):
            flush()
            units.append(line)
        else:
            current.append(line)
    flush()
    return units


def chunk_text(text: str, size: int = 700, overlap: int = 120):
    """Create overlapping line-aware chunks without splitting technical rows.

    Chunks stay within the requested word target except when a single heading or
    table row itself is longer. Overlap is applied at complete-unit boundaries.
    """
    text = text.strip()
    if not text:
        return []
    if size < 1 or overlap < 0:
        raise ValueError("size must be positive and overlap must not be negative")
    if len(text.split()) <= size:
        return [text]
    if overlap >= size:
        raise ValueError("overlap must be smaller than size when chunking is required")

    units = _units(text)
    expanded: list[str] = []
    for unit in units:
        if len(unit.split()) <= size or _TABLE_ROW.search(unit) or _HEADING.match(unit):
            expanded.append(unit)
            continue
        sentences = re.split(r"(?<=[.!?])\s+", unit)
        for sentence in sentences:
            words = sentence.split()
            if len(words) <= size:
                expanded.append(sentence)
            else:
                expanded.extend(words)
    units = expanded
    if sum(len(unit.split()) for unit in units) <= size:
        return [text]

    chunks: list[str] = []
    seen_chunks: set[str] = set()
    start = 0
    active_heading = None
    while start < len(units):
        end = start
        word_count = 0
        while end < len(units):
            unit_words = len(units[end].split())
            if end > start and word_count + unit_words > size:
                break
            word_count += unit_words
            end += 1

        chunk_units = units[start:end]
        for unit in units[:start]:
            if _SECTION_HEADING.match(unit):
                active_heading = unit
        chunk = "\n".join(chunk_units).strip()
        if active_heading and active_heading not in chunk_units:
            chunk = f"{active_heading}\n{chunk}".strip()
        if chunk and chunk not in seen_chunks:
            chunks.append(chunk)
            seen_chunks.add(chunk)
        if end >= len(units):
            break

        # Retain whole lines/rows up to the overlap budget. Always move forward.
        next_start = end
        overlap_words = 0
        while next_start > start + 1:
            previous_words = len(units[next_start - 1].split())
            if overlap_words + previous_words > overlap:
                break
            overlap_words += previous_words
            next_start -= 1
        start = max(start + 1, next_start)

    return chunks
