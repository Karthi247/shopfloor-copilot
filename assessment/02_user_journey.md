# User journey

1. A supervisor opens the workspace on a phone, tablet or desktop and sees the index status.
2. They enter a natural-language question or choose a shift quick action.
3. The interface shows that document search is running and prevents duplicate submission.
4. The backend retrieves page-level passages from the local vector index. For a current question it excludes superseded revisions; an explicitly requested historical revision can still be selected.
5. If evidence passes the configured relevance and lexical-anchor checks, the configured LLM receives only those excerpts. Otherwise the application displays the fixed no-answer wording.
6. The supervisor reads the concise answer, revision note, citations and page number; safety-related questions receive a visible warning treatment.
7. If the response is unsupported or ambiguous, the supervisor consults the source procedure or authorized department.

## Failure and recovery

- Empty index: run the separate indexing command and verify its result.
- Provider unavailable or key missing: display a backend error, then configure the provider or consult the official document.
- Weak retrieval: return the no-answer response rather than guessing.
- Conflicting or unclear controlled documents: escalate to the document owner; the UI is not an approval system.

The prototype does not authenticate users, provide emergency response, or replace posted controls and authorized supervision.
