# Architecture

SovereignAI Phase 1 is a local-first Retrieval-Augmented Generation (RAG) app.

```
React (Vite, :5173) ──HTTP/JSON──> FastAPI (:8000) ──> services
                                                   ├─ pdf_service       PyMuPDF text + validation
                                                   ├─ ocr_service       Tesseract fallback (scanned pages)
                                                   ├─ chunking_service  overlapping chunks + page numbers
                                                   ├─ embedding_service Sentence Transformers (local)
                                                   ├─ vector_store      FAISS (one index file per document)
                                                   ├─ local_llm         Ollama on 127.0.0.1:11434
                                                   ├─ rag_service       ingest + ask orchestration
                                                   └─ audit_service     metadata-only audit events
SQLite: documents, chunks (text + page), audit_events
Disk:   data/uploads, data/extracted, data/indexes, data/audit_logs
```

## Upload flow
1. Validate extension, size, `%PDF-` header, and that PyMuPDF can open it (no password, >0 pages).
2. Store as `data/uploads/<uuid>.pdf` (server-generated name; the original name is sanitized and kept only for display).
3. Extract text per page. Pages with almost no text are OCR'd if Tesseract is installed.
4. Chunk (default 900 chars, 150 overlap), embed locally, write a FAISS index, store chunk text/page in SQLite.
5. Identical files (same SHA-256) reuse the existing index instead of re-embedding.

## Question flow
1. Embed the question, search the FAISS index of each selected document, keep the top-K hits above `MIN_RELEVANCE_SCORE`.
2. No relevant hits -> "could not find" answer, and the model is **not** called.
3. Otherwise only those chunks + the question go to Ollama inside `<context>` blocks. The system prompt tells the model to treat context as untrusted data, never follow instructions in it, and reply `NOT_FOUND` when unsupported (mapped to the same "could not find" message).
4. Citations come from the retrieved chunks (document, page, excerpt), never from model output, so they cannot be invented.

## Extending to Phases 2/3
New file types plug in next to `pdf_service` (produce `PageText` lists); model routing replaces the single call in `local_llm.generate`; agent steps and report generation can be new services calling `rag_service.ask`.
