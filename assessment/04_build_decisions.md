# Build decisions

- **FastAPI:** provides a small typed HTTP API and built-in OpenAPI docs for the React client.
- **RAG:** retrieval grounds answers in company passages and enables citations instead of treating a general chatbot response as procedure.
- **ChromaDB:** persistent local vector storage fits a small local pilot and keeps ingestion separate from queries.
- **Local embeddings:** Sentence Transformers embeds documents and queries without sending the source corpus to an external embedding service.
- **Groq initially:** a configurable remote generation provider is implemented behind an adapter. Credentials remain on the backend. No key is included.
- **Ollama alternative:** an HTTP adapter uses Ollama's local chat endpoint; switch via `LLM_PROVIDER=ollama` and configure its model. It still requires installation and runtime verification.
- **Revision handling:** document number, revision and effective date metadata are stored per chunk. Current queries select the latest effective revision when dates are known, and fall back to the highest revision number when a date is missing. Explicit historical queries retain that revision; comparisons naming two revisions retrieve both. Old chunks remain in ChromaDB.
- **Quick actions:** common maintenance, inspection and safety entry points reduce typing on a shared shop-floor device. They submit normal questions to retrieval rather than fixed answers.
- **Hallucination controls:** a distance threshold plus lexical-anchor gate, fixed no-answer response, excerpt-only generation prompt, citations, and safety styling. These controls reduce risk but cannot certify an answer; source verification remains necessary.

## Known engineering gaps

Revision applicability uses effective dates when all dates are available; it falls back to revision number when dates are missing and flags incomplete metadata in the response. The lexical check is intentionally conservative and can reject valid semantic matches. Table extraction uses PyMuPDF's sorted text output and needs fixture validation. There is no user authentication, document approval workflow, answer audit store, or offline emergency behavior.
