def chunk_text(text: str, size: int = 700, overlap: int = 120):
    if len(text.split()) <= size:
        return [text.strip()] if text.strip() else []
    words = text.split()
    step = max(1, size - overlap)
    return [
        " ".join(words[i : i + size])
        for i in range(0, len(words), step)
        if words[i : i + size]
    ]
