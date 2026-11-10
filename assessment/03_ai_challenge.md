# AI challenge notes (AI-generated critique)

This is a critique draft for review. It does not claim that another AI system or a user interview was conducted. Complete the personal reflection only from actual experience.

## Original journey assumptions

The journey assumes the right PDF is indexed, searchable text is extractable, metadata is reliable, the supervisor can read the answer, and network access to the local server is available. These assumptions need validation on the factory floor.

## Skeptical questions

- What happens if a PDF is scanned, its text order is wrong, or a table loses column relationships?
- How does an operator know a document is current and formally approved?
- Can a retrieved excerpt be topically similar yet fail to answer the actual question?
- Is excluding older revision chunks enough when revision dates or applicability are ambiguous?
- Does the screen remain legible with gloves, glare, noise, and a small phone?
- What is the expected action in an emergency if the local Wi-Fi or service is unavailable?
- Who can trigger re-indexing, and how is document integrity checked?

## Key critique points and suggested changes

- Treat extraction and metadata verification as a controlled ingestion review, especially for tables and scanned pages.
- Establish a formally approved source of truth, audit trail, access control, and role-based authorization before deployment.
- Add evaluation cases for unanswerable questions, conflicts, historical revisions, and near-miss retrievals.
- Show uncertainty and source excerpts so users can independently verify statements.
- Validate with operators under real device and network conditions; support a clear offline fallback to controlled procedures.
- Keep explicit emergency instructions within approved emergency procedures, and do not present a chatbot as emergency authority.

## Personal reflection — complete honestly

- What did I observe directly?
- What did I change after testing with a real user?
- Which assumptions proved wrong?
- What did I personally find difficult?
- What evidence supports each conclusion?
