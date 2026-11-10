from app.services.chunking import chunk_text


def test_chunks_overlap():
    words = [f"w{i}" for i in range(18)]
    chunks = chunk_text(" ".join(words), size=10, overlap=3)
    assert chunks[0].split()[-3:] == chunks[1].split()[:3]


def test_short_chunks_preserve_table_rows():
    source = "Lot size       Samples\n2 - 5          All pieces"
    assert chunk_text(source, size=20) == [source]
