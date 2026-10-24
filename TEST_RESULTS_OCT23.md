# RAG and Security Verification

## Automated test suite

- Latest command: `python -m pytest -q --ignore=test_docx_styles.py`
- Latest run: October 24, 2026, from `backend/` with the project virtual environment and local PostgreSQL running, after replacing deprecated naive UTC timestamp defaults with timezone-aware UTC values.
- Latest result: **83 passed in 76.97 seconds**, with no warnings.
- This latest result replaces the earlier October 23 count of 81 passed and the October 24 run that still emitted a deprecation warning.
- `test_docx_styles.py` was excluded because it is a standalone DOCX inspection script that attempts to open a local document during collection; it is not a normal automated test and the expected local fixture is unavailable in this run.
- An initial attempt to run `Set-Location .\backend` failed because the terminal was already in `backend/`. This was only a working-directory mistake and did not affect the test result.

## Retrieval evaluation

- 15 evaluated questions: 9 answerable and 6 unanswerable.
- Results: 9 true positives, 0 false negatives, 6 true negatives, 0 false positives.
- All 9 answerable questions retrieved their expected sections.

## RAG behavior checks

- Authenticated `POST /rag/ask`, question `What is a UAV?`: **200**, grounded answer returned with 2 citations from `Q1.docx` (document 5, chunks 165 and 171).
- Unsupported question `Who approves an employee's leave request?`: **200**, returned the configured insufficient-information response and an empty citations list.
- The direct RAG service check for an unsupported question also returned the insufficient-information response with no citations.
- DOCX citation page numbers were `null` in the tested result; page-level citation data remains a known limitation for this document.

## Retrieval components covered

Automated tests and the retrieval evaluation cover the hybrid vector and PostgreSQL full-text search path, reciprocal-rank fusion, reranking, retrieval metadata, evidence sufficiency, context/prompt construction, answer validation, and citations. The results above preserve the previously passing evidence-sufficiency and evaluation behavior.

## Authentication, authorization, and tenant-isolation checks

- Protected document listing without authentication: **401 Not authenticated**.
- Admin account (`document.tester@example.com`, role `admin`) called `GET /users/admin/all`: **200**.
- Regular test account called `GET /users/admin/all`: **403 Admin access required**.
- Regular user's `GET /documents/`: **200**, empty list.
- Regular user's `GET /documents/search` for `transportation`: **200**, empty list.
- Regular user's `GET /conversations`: **200**, empty list before creating its test conversation.
- Regular test account created conversation ID 4; admin's `GET /conversations/4`: **404 Conversation not found**.
- Refresh-token rotation was verified earlier: reuse of the revoked refresh token returned **401 Refresh token has been revoked**.

## Status and follow-up

The Oct 23 verification goal is complete for the checks recorded above. The automated suite passes with the DOCX inspection helper excluded. The helper's collection behavior and null DOCX page citations are known limitations to assess separately; neither invalidated the passing suite or RAG answer/refusal checks.
