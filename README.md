# SovereignAI — local PDF question answering (Phase 1)

Upload PDFs, ask questions in a chat, get answers grounded in the documents with **page numbers and supporting excerpts**. Everything runs on your computer: local LLM (Ollama), local embeddings (Sentence Transformers), local vector search (FAISS), local database (SQLite). No cloud AI API is used and document contents are never sent to an external AI service.

> **Verification status (please read):** the code was written and every Python file passes a syntax check, but in the environment where it was generated the package registries (PyPI, npm) were blocked, so the backend tests, the frontend build and the real Ollama/embedding flow have **not been run**. Run the commands below on your PC; if something fails, the troubleshooting section and the error text will point to the fix.

## Architecture (short)
React UI → FastAPI → services (PDF extraction → OCR fallback → chunking → embeddings → FAISS) → Ollama. SQLite stores document/chunk metadata; files live under `backend/data/`. Details: [docs/architecture.md](docs/architecture.md).

## Folder structure
```
SovereignAI/
├── README.md  .gitignore  .env.example  requirements.txt  docker-compose.yml
├── backend/
│   ├── requirements.txt  .env.example  pytest.ini
│   ├── data/{uploads,extracted,indexes,audit_logs}/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/routes/{health,documents,chat}.py
│   │   ├── core/{config,logging_config}.py
│   │   ├── schemas/{documents,chat}.py
│   │   ├── database/{database,models}.py
│   │   └── services/{pdf,ocr,chunking,embedding,vector_store,local_llm,rag,audit}_service.py
│   └── tests/{conftest,test_pdf_service,test_chunking,test_rag_service,test_api}.py
├── frontend/  (React + TypeScript + Vite; src/components, api, types, styles)
├── docs/{architecture,testing}.md
└── scripts/{run_backend,run_frontend}.bat
```
Changes from the brief: added `backend/pytest.ini`, `backend/tests/{__init__,conftest}.py`, `backend/app/**/__init__.py` files, `frontend/src/vite-env.d.ts`, and a `DATA_DIR` setting (used by tests to isolate storage). `database/models.py` holds plain SQL helper functions rather than an ORM, to keep it beginner-friendly.

## Prerequisites (Windows 10/11)
- Python 3.11+ (3.11 or 3.12 recommended; some ML packages lag behind the newest Python) — https://www.python.org/downloads/ (tick "Add python.exe to PATH")
- Node.js 20+ LTS — https://nodejs.org
- Ollama — https://ollama.com/download
- Optional, only for scanned PDFs: Tesseract OCR (e.g. the UB Mannheim Windows installer). Default path `C:\Program Files\Tesseract-OCR\tesseract.exe` is auto-detected; otherwise set `TESSERACT_CMD`.
- ~5 GB free disk, 8 GB RAM recommended.
- **Internet is needed once** to download the Ollama model (~2 GB) and the embedding model (~90 MB) and to install packages. Afterwards everything works offline. Your documents are never uploaded.

## Setup and run (PowerShell or Command Prompt)

**1. Check tools**
```
python --version
node --version
ollama --version
```

**2. Download the local model**
```
ollama pull llama3.2:3b
```
(Ollama runs in the background after installation. If not: `ollama serve`.)

**3. Backend**
```
cd SovereignAI\backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```
(PowerShell may block activation: run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.) Check http://127.0.0.1:8000/api/health and the API docs at http://127.0.0.1:8000/docs.
`scripts\run_backend.bat` does the same steps.

**4. Frontend** (second terminal)
```
cd SovereignAI\frontend
npm install
npm run dev
```
`scripts\run_frontend.bat` does the same.

**5. Open** http://localhost:5173

The first upload is slower because the embedding model is downloaded and loaded.

## Test with a sample PDF
Create one (with the backend venv active):
```
python -c "import fitz; d=fitz.open(); p=d.new_page(); p.insert_text((72,72),'Warranty terms: the warranty period is 24 months from purchase.'); p=d.new_page(); p.insert_text((72,72),'Installation: mount the unit on a flat wall with the supplied screws.'); d.save('sample.pdf')"
```
Upload `sample.pdf`, tick it, then try:
- "How long is the warranty?" → answer citing page 1.
- "How do I install it?" → citing page 2.
- "Who won the 2010 World Cup?" → "could not find an answer in the available document content."

Automated tests: `cd backend && python -m pytest -v` (no models needed) and `cd frontend && npm run build`. See [docs/testing.md](docs/testing.md).

## Configuration
Copy `backend/.env.example` to `backend/.env`. Key settings: `OLLAMA_MODEL`, `EMBEDDING_MODEL`, `MAX_UPLOAD_MB`, `TOP_K`, `CHUNK_SIZE`, `CHUNK_OVERLAP`, `MIN_RELEVANCE_SCORE` (raise if irrelevant text gets cited, lower if good questions are refused), `OLLAMA_TIMEOUT_SECONDS`, `CORS_ORIGINS`. Values are validated at startup. If you change `EMBEDDING_MODEL`, re-upload your documents (existing indexes use the old model).

## Troubleshooting
| Symptom | Fix |
|---|---|
| Status shows "Ollama is not reachable" | Start Ollama (`ollama serve` or the tray app); check `http://127.0.0.1:11434`. |
| "Model 'llama3.2:3b' not installed" | `ollama pull llama3.2:3b`, or change `OLLAMA_MODEL` to an installed model. |
| Answers time out | First request loads the model into RAM. Raise `OLLAMA_TIMEOUT_SECONDS` or use a smaller model. |
| `pip install` fails on faiss-cpu / torch | Use Python 3.11 or 3.12 (64-bit); upgrade pip: `python -m pip install -U pip`. |
| Upload says "Could not create embeddings" | The embedding model could not be downloaded (needs internet once) or disk is full. Retry; check the backend console. |
| "PDF looks scanned and needs OCR" | Install Tesseract and restart the backend, or set `TESSERACT_CMD`. |
| Browser: "Cannot reach the backend" | Backend not running on port 8000, or CORS: frontend must be served from `localhost:5173`/`127.0.0.1:5173`. |
| Port already in use | Change `BACKEND_PORT`/uvicorn `--port`; for the frontend, edit `frontend/vite.config.ts`. If you change ports, update `CORS_ORIGINS` and set `VITE_API_URL`. |
| `.venv\Scripts\activate` blocked | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| Every question gets "could not find" | Lower `MIN_RELEVANCE_SCORE` (e.g. 0.1), or the PDF text may be poor. |

## Security notes and limitations (single-user prototype)
Implemented: localhost binding, CORS limited to the local frontend, file type/size/header/open validation, sanitized display names, server-generated IDs, path-traversal guards, document text treated as untrusted data in prompts, no document text or prompts in logs/audit events (metadata only: ids, counts, error types), deletion removes PDF, extracted text, index and DB rows, no secrets in code.
Not provided: **no authentication or user accounts** (anyone who can reach the port can use it — keep it on localhost), **no encryption at rest** (files and SQLite are plain on disk; use BitLocker), no rate limiting, and prompt-injection mitigation reduces but cannot eliminate the risk with a small local model. Extracted text (`data/extracted`) and uploaded PDFs are stored unencrypted until you delete the document.

## Roadmap
Phase 2 (Word/text files, summaries, audit dashboard, better retrieval) and Phase 3 (model routing, agents, drawings, spreadsheets, sandboxed code) are intentionally not implemented; the service layout is designed so they can be added.
