# Testing

## Backend (pytest)
```
cd backend
.venv\Scripts\activate
python -m pytest -v
```
The tests use temporary storage, a fake deterministic embedding function and a fake LLM, so they need **no model downloads, no Ollama and no Tesseract**. They cover: filename sanitizing, PDF validation, page-number-preserving extraction, chunking/overlap, ingest, retrieval with citations, "not found" behaviour, prompt-injection containment, LLM-unavailable handling, deletion of all stored data, and the HTTP API lifecycle (upload, list, get, ask, delete, error codes).

## Frontend build validation
```
cd frontend
npm install
npm run build
```
This type-checks (`tsc --noEmit`) and produces a production bundle.

## Manual end-to-end test
See "Test with a sample PDF" in the README. This is the only test that exercises the real embedding model and Ollama.

## Status
The test files were written together with the code. They have to be run on your machine to confirm they pass; see the README for the honest verification status.
