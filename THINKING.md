# ShopFloor AI Copilot — Thinking and Reflection

## 1. Understand the user

The primary users are shop-floor supervisors who need to find an approved work instruction quickly, often during a shift and from a phone. Quality, maintenance, and safety staff also need to consult their relevant procedures.

The answer must be concise and traceable to a source document, revision, and page so the user can verify it. The assistant should say when it cannot find sufficient evidence. It must not replace controlled documents, posted safety controls, or authorized supervision.

The project assumes the supplied PDFs are approved and current, their document numbers and revisions can be identified, and the first deployment is a trusted private network. These assumptions still need confirmation with the customer. Important open questions include who approves revisions, how obsolete documents are marked, what access restrictions apply, which languages and devices are needed, and what users should do when the system is unavailable.

## 2. User journey

1. A supervisor opens the workspace on a phone, tablet, or desktop and checks the index status.
2. They type a question or choose a common shop-floor question.
3. The interface indicates that the request is in progress and prevents duplicate submissions.
4. The backend searches page-level passages in the local vector index. Current questions prioritize the applicable revision; explicit historical questions can retrieve an older revision.
5. When retrieved evidence passes relevance and lexical checks, the configured language model receives those excerpts. If evidence is insufficient, the app returns its fixed no-answer response.
6. The supervisor reviews the answer, revision information, citations, and page numbers. Safety-related answers receive a visible warning treatment.
7. If the answer is missing, ambiguous, or unsupported, the supervisor checks the controlled procedure or escalates to an authorized person.

Recovery paths include indexing documents when the index is empty, checking provider configuration when generation is unavailable, and consulting the official procedure when retrieval is weak or documents conflict. The prototype does not provide emergency response or an approval workflow.

## 3. AI challenge – conversation excerpts and reflection

The central AI challenge is deciding when retrieved text actually supports an operational answer. A passage can be topically similar without answering the user's question; revision metadata, PDF extraction, and tables can also be incomplete. The system therefore combines retrieval with relevance and lexical checks, supplies the model only retrieved excerpts, requires citations, and uses a fixed response when support is insufficient. These controls reduce unsupported answers but cannot certify correctness.

Examples of user needs represented in the project conversation:

> “Who is authorized to remove a Lockout/Tagout (LOTO) lock?”

> “The machine is showing alarm AL-104. What does it mean and what should the operator do?”

These examples show why the assistant needs evidence that answers the specific question, not merely a passage mentioning LOTO or machine alarms. The answer should identify the source and leave the operator able to verify it.

This project record does not claim that formal interviews or factory-floor usability tests were conducted. Before deployment, the assumptions should be checked with supervisors and document owners, including how the system behaves for scanned PDFs, ambiguous revisions, conflicting procedures, weak Wi-Fi, and emergency situations.

## 4. The improvement you added and why you chose it

I added a deterministic test for the LOTO answer-service path. It supplies mocked excerpts from both relevant procedure pages and a mocked language-model provider, then checks that the answer service assembles the complete evidence context and returns an answer. This was chosen because the test previously depended on a populated local Chroma index, which is not present in a clean CI environment. The test now checks answer-service behavior without requiring a local index or a live Groq call.

Other design choices supporting the same goal include page-level citations, revision metadata and filtering, a conservative no-answer path, and a retry option for transient request failures. These help users verify and recover, while leaving decisions with the people responsible for the work.

## 5. Final reflection – biggest challenge and how you handled it

The biggest engineering challenge recorded in this project was making retrieval and answer behavior dependable across different document and runtime states. A live local index can make a test pass even when CI has no indexed documents. For the LOTO answer-service test, I removed that environmental dependency by providing explicit procedure excerpts and a fake provider. The targeted test passed, and the full backend suite passed locally with 30 tests passing.

The remaining challenge is validating the source data and workflow with actual users. PDF extraction can lose table structure, revision metadata can be incomplete, and retrieval thresholds can reject valid questions or accept weak matches. These need representative document fixtures and review with supervisors and document owners. This prototype has not been shown to certify procedures or replace an approved source of truth.

