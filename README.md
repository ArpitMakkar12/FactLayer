# FactLayer — Every fact traced to its source, every conflict explained.

> **SuperJoin VIT 2026 Intern Assignment**
> Extract grounded facts from PDFs → link to source evidence → identify corroboration, contradiction, and reconciliation across documents.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green)
![Tests](https://img.shields.io/badge/Tests-16%2F16%20passing-brightgreen)
![License](https://img.shields.io/badge/License-MIT-yellow)

[![Live Demo](https://img.shields.io/badge/Live%20Demo-View%20App-2563eb?style=for-the-badge&logo=railway&logoColor=white)](https://factlayer-production-f1bb.up.railway.app/)
[![Demo Video](https://img.shields.io/badge/Demo%20Video-Watch%20Now-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://youtu.be/UPfpCdo6Udk)

---

## Approach

```
PDF Upload → Parse Pages → Extract Facts → Verify Quotes → Normalize → Block Pairs → Judge Relations → Pin Cases
```

1. **Parse** — PyMuPDF extracts text per page (+ table cells). Files stored by SHA-256 hash for deduplication.
2. **Extract** — Heuristic regex extractor (always available) + optional LLM extractor (if `LLM_API_KEY` set). Pages processed in configurable batches.
3. **Verify** — Every candidate quote is checked against actual page text (NFKC-normalized, whitespace-collapsed substring match). Failed quotes are logged as failures, never shown as facts.
4. **Normalize** — Period (`FY 2023-24` → `FY2024`) and unit (`crore` → `INR_crore`) normalization. Raw values always preserved. Dynamic attributes stored in `extra_json`.
5. **Block** — Token-overlap candidate pairs generated incrementally (only new facts paired against all existing facts). Jaccard similarity with predicate boosting.
6. **Judge** — Each candidate pair classified as `corroborates`, `contradicts`, `reconciled` (with axis: time/units/scope/definition), or `unrelated`. Period safety gate prevents cross-period contradictions.

**No hardcoded facts, filenames, or document-specific rules.** A new PDF uses the exact same pipeline.

---

## Quick Start

### Prerequisites
- Python 3.11+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/<your-username>/SuperJoin.git
cd SuperJoin

# Create virtual environment
python -m venv .venv

# Activate it
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment config
cp .env.example .env
```

### Run the Server

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Open **http://localhost:8000** in your browser.

### Upload PDFs

1. Navigate to the **Upload** tab
2. Drag and drop PDFs (or click to browse)
3. Optionally tag with a collection name (e.g., "Delhivery")
4. Wait for ingestion to complete — facts and relations appear automatically

### Run Tests

```bash
# From project root
pytest -v
```

---

## Four Required Cases

Cases are **pinned from live pipeline output**, not hardcoded. Visit `/#/cases` to inspect them.

| Slot | Case | How It's Produced |
|------|------|-------------------|
| **1** | Corroborated across documents | Same metric, compatible values, different wording → `corroborates` |
| **2** | Genuine or likely contradiction | Same entity, period, scope; incompatible values → `contradicts` |
| **3** | Apparent contradiction explained by context | Looks like conflict until time/units/scope applied → `reconciled` with axis |
| **4** | Extraction or reasoning failure | Quote verification drop or pipeline error → logged in `failures` table |

Each case shows **both facts' verbatim quotes, page numbers, and source documents**.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/stats` | Dashboard counts (documents, facts, relations, failures) |
| `GET` | `/api/v1/documents` | List all documents with fact/relation counts |
| `POST` | `/api/v1/documents` | Upload a PDF (multipart/form-data) |
| `DELETE` | `/api/v1/documents/{id}` | Delete document + cascade facts/relations |
| `POST` | `/api/v1/documents/{id}/ingest` | Trigger background ingestion |
| `GET` | `/api/v1/facts?q=&limit=&cursor=` | Search and paginate facts |
| `GET` | `/api/v1/relations?type=&q=&limit=&offset=` | Search and filter relations |
| `GET` | `/api/v1/failures?q=&limit=&offset=` | Browse extraction failures |
| `GET` | `/api/v1/cases` | The four showcase cases |
| `GET` | `/health` | Health check |

---

## Brownie Points

| Extension | Implementation | Proof |
|-----------|---------------|-------|
| **Large PDFs** | Page batching (`BATCH_PAGES=3`), skip short pages, background job + polling | Upload 100-page PDF; UI shows progress then ready |
| **Many PDFs, one layer** | Single flat fact table; new facts compared against all existing | Second PDF creates cross-document relations |
| **Dynamic schema** | `facts.extra_json` stores arbitrary attributes (`listing_venue`, `rating`, etc.) | UI renders unknown keys dynamically in fact detail |
| **Incremental ingestion** | SHA-256 reuse; skip when `status=ready`; pairs only involve new fact IDs | Re-POST same file → `reused: true`, no rebuild |

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | **FastAPI** (Python 3.11+) |
| Database | **SQLite** (WAL mode, foreign keys) |
| PDF Parsing | **PyMuPDF** (pymupdf) |
| ORM | **SQLAlchemy 2.0** (declarative) |
| Frontend | **Vanilla JS** SPA (no framework, no build step) |
| Styling | Custom CSS with dark/light theme |
| Tests | **pytest** (16 tests) |

---

## Project Structure

```
SuperJoin/
├── backend/
│   └── app/
│       ├── api/          # FastAPI route handlers
│       │   ├── cases.py      # 4 showcase cases
│       │   ├── documents.py  # Upload, list, delete, ingest
│       │   ├── facts.py      # Search & paginate facts
│       │   ├── failures.py   # Browse failures
│       │   ├── relations.py  # Search & filter relations
│       │   └── samples.py    # Dump/load sample data
│       ├── db/           # ORM models & session
│       │   ├── orm.py        # Document, Page, Fact, Relation, Case, Failure, Job
│       │   └── session.py    # Engine, WAL, migrations
│       ├── extract/      # Fact extraction pipeline
│       │   ├── heuristic.py  # Regex + LLM extraction
│       │   ├── verify.py     # Quote verification gate
│       │   ├── schema.py     # Pydantic fact schema
│       │   └── extra.py      # Dynamic attribute extraction
│       ├── jobs/         # Pipeline orchestration
│       │   ├── pipeline.py   # Main ingest workflow
│       │   └── samples.py    # Sample data import/export
│       ├── link/         # Relation discovery
│       │   ├── block.py      # Candidate pair blocking (Jaccard)
│       │   ├── embed.py      # Token embedding
│       │   └── judge.py      # Relation classification
│       ├── web/          # Frontend SPA
│       │   ├── index.html
│       │   ├── app.js
│       │   └── styles.css
│       ├── main.py       # FastAPI app setup
│       └── settings.py   # Configuration
├── tests/                # 16 passing tests
├── docs/                 # Design documents (PRD, HLD, LLD)
├── starter-datasets/     # Provided PDFs
├── requirements.txt
└── .env.example
```

---

## Design Decisions & Trade-offs

1. **Quote verification as the core gate** — Every extracted fact must have a verbatim quote that exists in the source page. This prevents hallucinated or approximate claims from entering the knowledge layer. Trade-off: some valid facts with paraphrased quotes are dropped.

2. **Period contradiction safety gate** — Facts from different time periods (e.g., FY2023 vs FY2024) are never labeled as contradictions, even if their values differ. They are reconciled on axis `time`. This prevents false positives that would be misleading.

3. **Token Jaccard over vector embeddings** — We use simple token-overlap for candidate blocking instead of hosted vector search. Trade-off: misses semantic synonyms, but works fully offline with zero external dependencies.

4. **Incremental over full-rebuild** — New documents only pair their facts against existing ones. Re-uploading the same file (by SHA-256) is a no-op. Trade-off: if extraction logic changes, old facts aren't re-extracted (by design).

5. **Vanilla JS over React/Vue** — The frontend is a single `app.js` file with no build step. Trade-off: less ecosystem tooling, but zero setup friction and instant deployment.

---

## Honest Limits

- Local extractor is precision-oriented; dense financial tables may need an LLM key for full coverage.
- Embeddings are token Jaccard, not a hosted vector DB (deliberate MVP cut for offline operation).
- SQLite is single-writer; high-concurrency production use would need PostgreSQL.

---

## Design Documentation

See [docs/README.md](docs/README.md) for:
- Product Requirements Document (PRD)
- High-Level Design (HLD)
- Low-Level Design (LLD)
- Tech Stack rationale
- Implementation Plan

---

## License

MIT
