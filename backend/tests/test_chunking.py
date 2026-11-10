from app.services.chunking import chunk_text


def test_chunks_overlap():
    words = [f"w{i}" for i in range(18)]
    chunks = chunk_text(" ".join(words), size=10, overlap=3)
    assert chunks[0].split()[-3:] == chunks[1].split()[:3]


def test_long_table_rows_and_headings_remain_whole():
    heading = "4. Sampling Plan"
    rows = [
        f"Lot size: {index} - {index + 4} | Samples to inspect: 32"
        for index in range(0, 30, 5)
    ]
    chunks = chunk_text("\n".join([heading, *rows]), size=18, overlap=4)
    assert all(heading in chunk for chunk in chunks)
    for row in rows:
        assert sum(row in chunk for chunk in chunks) == 1


def test_chunking_does_not_return_duplicate_chunks():
    text = "\n\n".join(
        f"Section {index}. " + "A technical procedure line with details. " * 4
        for index in range(8)
    )
    chunks = chunk_text(text, size=24, overlap=6)
    assert len(chunks) == len(set(chunks))


def test_short_chunks_preserve_table_rows():
    source = "Lot size       Samples\n2 - 5          All pieces"
    assert chunk_text(source, size=20) == [source]
