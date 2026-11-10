import hashlib
import json
import re
from pathlib import Path

import chromadb
import fitz

from app.config import settings
from app.services.chunking import CHUNKING_VERSION, chunk_text
from app.services.embedding_service import load_embedding_model


def metadata_for(filename: str, page_text: str):
    text = f"{filename} {page_text[:1500]}"
    doc = re.search(
        r"(?<![A-Z0-9-])(QC-SOP-\d{3}|MNT-MAN-[A-Z0-9]+(?:-[A-Z0-9]+)*|SAF-SOP-\d{3})(?![A-Z0-9-])",
        text,
        re.I,
    )
    rev = re.search(r"\bRev(?:ision)?\s*0?(\d+)\b", text, re.I) or re.search(
        r"_Rev0?(\d+)_", filename, re.I
    )
    title_match = re.search(r"(?:TITLE|DOCUMENT TITLE)\s*[:\-]\s*(.+)", page_text, re.I)
    effective = re.search(
        r"EFFECTIVE DATE\s*[:\-]?\s*(\d{1,2}[-/ ][A-Za-z]{3,9}[-/ ]\d{4}|\d{1,2}[-/]\d{1,2}[-/]\d{4})",
        page_text,
        re.I,
    )
    lines = [line.strip() for line in page_text.splitlines() if line.strip()]
    title_value = title_match.group(1).strip() if title_match else None
    if not title_value:
        doc_line = next(
            (
                i
                for i, line in enumerate(lines)
                if re.search(r"Document\s+No\.?", line, re.I)
            ),
            None,
        )
        if doc_line is not None and doc_line > 0:
            title_value = lines[doc_line - 1]
    headings = []
    for line in page_text.splitlines():
        heading = re.match(r"\s*(\d+(?:\.\d+)*\.)\s+([A-Z][^\r\n]{2,100})", line)
        words = heading.group(2).split() if heading else []
        title_case = len(words) == 1 or (len(words) >= 2 and words[1][:1].isupper())
        if heading and title_case and len(words) <= 8:
            headings.append(f"{heading.group(1)} {heading.group(2).strip()}")
    return {
        "document_number": doc.group(1).upper() if doc else "UNKNOWN",
        "revision": int(rev.group(1)) if rev else 0,
        "revision_known": bool(rev),
        "title": (
            title_value[:160] if title_value else Path(filename).stem.replace("_", " ")
        ),
        "effective_date": effective.group(1).strip()[:80] if effective else "Unknown",
        "section_heading": (
            "; ".join(dict.fromkeys(headings))[:240]
            if headings
            else "Section not identified"
        ),
        "filename": filename,
    }


def extract_page_text(page):
    body = re.sub(r"[ \t]+", " ", page.get_text("text", sort=True))
    body = re.sub(r"\n{2,}", "\n", body).strip()
    try:
        tables = page.find_tables().tables
    except Exception:
        tables = []
    table_rows = []
    for table in tables:
        rows = table.extract()
        if len(rows) < 2:
            continue
        headers = [" ".join(str(value or "").split()) for value in rows[0]]
        for row in rows[1:]:
            cells = [" ".join(str(value or "").split()) for value in row]
            paired = [
                f"{headers[index] or f'Column {index + 1}'}: {value}"
                for index, value in enumerate(cells)
                if value
            ]
            if paired:
                table_rows.append(" | ".join(paired))
    if table_rows:
        body += "\n\nStructured table rows:\n" + "\n".join(table_rows)
    return body


def ingest_documents(force: bool = False):
    settings.chroma_path.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(settings.chroma_path))
    collection = client.get_or_create_collection(
        "shopfloor_documents", metadata={"hnsw:space": "cosine"}
    )
    model = load_embedding_model()
    # Sample_Questions.pdf is the evaluation input, never an answer source.
    files = sorted(
        p
        for p in settings.documents_path.glob("*.pdf")
        if p.stem.lower() != "sample_questions"
    )
    indexed = 0
    for path in files:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        existing = collection.get(where={"filename": path.name}, include=["metadatas"])
        current_version = [
            meta
            for meta in existing["metadatas"]
            if meta.get("file_hash") == digest
            and meta.get("chunking_version") == CHUNKING_VERSION
        ]
        obsolete_ids = [
            ident
            for ident, meta in zip(existing["ids"], existing["metadatas"])
            if meta.get("file_hash") != digest
            or meta.get("chunking_version") != CHUNKING_VERSION
        ]
        if (
            existing["ids"]
            and not force
            and len(current_version) == len(existing["ids"])
        ):
            continue
        pdf = fitz.open(path)
        document_base = (
            metadata_for(path.name, pdf[0].get_text("text", sort=True))
            if len(pdf)
            else metadata_for(path.name, "")
        )
        ids, docs, metas = [], [], []
        for page_no, page in enumerate(pdf, 1):
            body = extract_page_text(page)
            if not body:
                continue
            page_metadata = metadata_for(path.name, body)
            base = {
                **document_base,
                "section_heading": page_metadata["section_heading"],
            }
            for ix, chunk in enumerate(chunk_text(body)):
                meta = {
                    **base,
                    "page": page_no,
                    "chunk": ix,
                    "file_hash": digest,
                    "chunking_version": CHUNKING_VERSION,
                }
                metadata_hash = hashlib.sha256(
                    json.dumps(meta, sort_keys=True).encode()
                ).hexdigest()[:8]
                ids.append(
                    f"{digest[:12]}-{CHUNKING_VERSION}-{page_no}-{ix}-{metadata_hash}"
                )
                docs.append(chunk)
                metas.append(meta)
        if docs:
            vectors = model.encode(docs, normalize_embeddings=True).tolist()
            collection.upsert(
                ids=ids, documents=docs, metadatas=metas, embeddings=vectors
            )
            if obsolete_ids:
                collection.delete(ids=obsolete_ids)
            indexed += 1
        elif obsolete_ids:
            collection.delete(ids=obsolete_ids)
    return {
        "files_found": len(files),
        "files_indexed": indexed,
        "chunks": collection.count(),
    }
