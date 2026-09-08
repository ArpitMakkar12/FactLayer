# Tech stack — FactLayer

**Document type:** Stack selection and rationale  
**Constraint:** Reviewer must run from README on a laptop.

## 1. Summary pick

| Layer | Choice | Why |
|---|---|---|
| Language | Python 3.12 | Best PDF + LLM ecosystem for a one-week build |
| API | FastAPI + Uvicorn | Multipart upload, OpenAPI, simple async |
| Validation | Pydantic v2 | HTTP + LLM JSON in one style |
| ORM | SQLAlchemy 2 + Alembic | Matches LLD tables; sqlite dialect |
| Database | SQLite WAL | Zero ops for hiring reviewers |
| PDF | PyMuPDF (`fitz`) | Page text + optional bbox; fast |
| Tables fallback | pdfplumber | Only if PyMuPDF tables are weak on a sample |
| LLM | Structured-output API (OpenAI or Gemini) | Extract + judge only |
| Embeddings | API embedding **or** `sentence-transformers` | Pair blocking |
| UI | Vite + React + TypeScript | Inspector that looks intentional |
| UI fallback | Jinja2 templates + HTMX | If React time-box is exceeded |
| Config | pydantic-settings + `.env` | Keys never committed |
| Tests | pytest | Verifier + relation gates |
| Lint/format | ruff | One tool |
| Package mgr | uv or pip + `requirements.lock` | Reproducible README |

## 2. Versions (targets)

Pin in lockfile at implement time. Intended bands:

- Python 3.12.x  
- fastapi ? 0.115  
- uvicorn[standard]  
- sqlalchemy ? 2.0  
- alembic  
- pydantic ? 2.8  
- pymupdf ? 1.24  
- httpx (LLM HTTP)  
- pytest ? 8  
- ruff  

Frontend (if used): Node 20+, Vite 6, React 18 or 19, react-router 6/7.

## 3. LLM usage policy

| Call | Input | Output | Model class |
|---|---|---|---|
| Extract | page/chunk text | `ExtractedPage` JSON | capable mini/flash |
| Judge | two facts + quotes | label + axis + explanation | can be smaller |
| Embed | subject+predicate+period | vector | small embedding |

**Not used:** agent loops, tool-calling chains, LangChain graphs. Direct SDK + our modules. LangChain/LlamaIndex add opacity the assignment punishes.

Offline/demo: `data/samples/*.json` loaded by a `--offline` flag so reviewers without keys see the four cases.

## 4. Rejected stack (and why)

| Rejected | Why not for MVP |
|---|---|
| Neo4j / Cypher | Assignment says graph viz is not the solution |
| Postgres + Docker Compose required | Extra friction for reviewers |
| Celery + Redis | No volume that justifies broker |
| Chroma / Pinecone | Blocking does not need a hosted vector DB |
| Next.js full-stack | Two runtimes; Python already required for PDF |
| Streamlit only | Acceptable fallback; weaker IA for cases/failures |
| Fine-tuned local 70B | Hardware lottery for evaluators |
| Kubernetes | Theatre |

## 5. Repo / runtime topology

```
browser  ?  :5173 Vite proxy /api  ?  :8000 uvicorn
                                      ?  SQLite file backend/app.db
                                      ?  data/uploads/
                                      ?  LLM HTTPS
```

Production-like split is unnecessary. CORS allow `localhost:5173`.

## 6. File size and security defaults

- Accept `application/pdf` only; sniff `%PDF` magic.  
- `MAX_UPLOAD_MB=25` (starter excerpts are ~100 pages; cap can be raised).  
- Path traversal: store only by `sha256`, never by user filename on disk.  
- Display filename sanitized.

## 7. What “dynamic schema” means in this stack

Not a runtime DDL explorer. It means:

- Fixed core columns (value, unit, period, scope, quote).  
- `extra_json` for newly seen attributes (`listing_venue`, `rating_agency`, …).  
- UI renders known keys if present; dumps the rest as key/value.

## 8. Implementation order vs stack

1. Python + SQLite + PyMuPDF + pytest (no LLM).  
2. Add LLM extract + verifier.  
3. Add FastAPI.  
4. Add link/judge.  
5. Add UI.  
6. Lock dependencies.

## 9. Cost control

- Batch pages.  
- Judge only blocked pairs.  
- Cache embeddings by `fact_id`.  
- Hash short-circuit full pipeline.

## 10. README stack contract

Reviewers need:

```
python -m venv
pip install -r requirements.txt
cp .env.example .env   # LLM_API_KEY
uvicorn app.main:app
# optional: npm ci && npm run dev
```

Plus: how to load `data/samples` without a key.
