import hashlib
from pathlib import Path

import pytest

from app.services import ingestion_service
from app.services.chunking import CHUNKING_VERSION


class FakeCollection:
    def __init__(self, records):
        self.records = records
        self.deleted = []

    def get(self, where=None, include=None):
        rows = [
            (ident, document, metadata)
            for ident, (document, metadata, _embedding) in self.records.items()
            if where is None or metadata.get("filename") == where.get("filename")
        ]
        return {
            "ids": [ident for ident, _document, _metadata in rows],
            "documents": [document for _ident, document, _metadata in rows],
            "metadatas": [metadata for _ident, _document, metadata in rows],
        }

    def upsert(self, ids, documents, metadatas, embeddings):
        for ident, document, metadata, embedding in zip(
            ids, documents, metadatas, embeddings
        ):
            self.records[ident] = (document, metadata, embedding)

    def delete(self, ids):
        self.deleted.extend(ids)
        for ident in ids:
            self.records.pop(ident, None)

    def count(self):
        return len(self.records)


class FakeClient:
    def __init__(self, collection):
        self.collection = collection

    def get_or_create_collection(self, *args, **kwargs):
        return self.collection


class FakeModel:
    def __init__(self, should_fail=False):
        self.should_fail = should_fail

    def encode(self, documents, normalize_embeddings=True):
        if self.should_fail:
            raise RuntimeError("embedding failure")
        return FakeVectors([[0.1, 0.2, 0.3] for _ in documents])


class FakeVectors(list):
    def tolist(self):
        return list(self)


@pytest.mark.parametrize("model_fails", [False, True])
def test_chunking_migration_stages_new_chunks_before_removing_old(
    monkeypatch, model_fails
):
    filename = "SAF-SOP-003_Lockout_Tagout_Procedure.pdf"
    documents = ingestion_service.settings.documents_path
    source = documents / filename
    file_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    old_id = "old-chunk"
    collection = FakeCollection(
        {
            old_id: (
                "old indexed text",
                {"filename": filename, "file_hash": file_hash},
                [0.0],
            )
        }
    )
    model = FakeModel(should_fail=model_fails)
    monkeypatch.setattr(ingestion_service.settings, "documents_path", documents)
    real_glob = Path.glob
    monkeypatch.setattr(
        Path,
        "glob",
        lambda path, pattern: (
            [source]
            if path == documents and pattern == "*.pdf"
            else real_glob(path, pattern)
        ),
    )
    monkeypatch.setattr(
        ingestion_service.chromadb,
        "PersistentClient",
        lambda **kwargs: FakeClient(collection),
    )
    monkeypatch.setattr(ingestion_service, "load_embedding_model", lambda: model)

    if model_fails:
        with pytest.raises(RuntimeError, match="embedding failure"):
            ingestion_service.ingest_documents()
        assert list(collection.records) == [old_id]
        assert not collection.deleted
    else:
        result = ingestion_service.ingest_documents()
        assert result["files_indexed"] == 1
        assert old_id in collection.deleted
        assert old_id not in collection.records
        assert all(
            metadata.get("chunking_version") == CHUNKING_VERSION
            for _document, metadata, _embedding in collection.records.values()
        )
