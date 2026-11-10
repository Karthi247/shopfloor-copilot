import json
import logging


def log_rag_event(logger: logging.Logger, event: str, **fields):
    """Emit one machine-readable RAG diagnostic event."""
    payload = {"event": event, **fields}
    logger.info("RAG_DIAGNOSTIC %s", json.dumps(payload, sort_keys=True, default=str))
