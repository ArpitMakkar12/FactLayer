# LLD — FactLayer low-level design

**Document type:** Low-level design  
**Companion:** [HLD](./HLD.md) · [TECH_STACK](./TECH_STACK.md)

## 1. Repository layout

```
backend/
  app/
    main.py                 # FastAPI app, CORS, static mount
    api/
      documents.py
      facts.py
      relations.py
      cases.py
      failures.py
      deps.py               # DB session
    domain/
      models.py             # dataclasses / enums
    ingest/
      pdf.py                # PyMuPDF
      tables.py
    extract/
      chunk.py
      prompts.py
      schema.py             # Pydantic LLM schema
      verify.py             # quote gate
    link/
      embed.py
      block.py
      judge.py
      prompts.py
    normalize/
      period.py
      units.py
      entity.py
    db/
      session.py
      orm.py
      migrate.py
    llm/
      client.py             # provider interface
      settings.py
    jobs/
      pipeline.py           # state machine runner
frontend/                   # Vite React inspector (optional cut)
data/uploads/               # gitignored
data/samples/               # committed JSON dumps
docs/
```

## 2. Document state machine

```
uploaded --parse_ok--> parsed --extract_ok--> extracted
extracted --normalize_ok--> normalized --judge_ok--> ready

any --fatal--> failed
```

`jobs` rows record `stage`, `attempts`, `error`. Retry is per-stage, max 3, exponential backoff on LLM 429.

## 3. ORM (logical schema)

### documents

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| filename | TEXT | display only |
| sha256 | CHAR(64) UNIQUE | idempotency |
| status | ENUM | see state machine |
| page_count | INT | |
| created_at, updated_at | DATETIME | |

### pages

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| document_id | FK | ON DELETE CASCADE |
| page_no | INT | 1-based file index |
| text | TEXT | extraction source of truth |
| UNIQUE(document_id, page_no) | | |

### tables

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| page_id | FK | |
| ordinal | INT | nth table on page |
| payload_json | JSON | cells |
| bbox_json | JSON nullable | if PyMuPDF gives it |

### facts

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| document_id | FK | |
| page_id | FK | |
| statement | TEXT | |
| subject | TEXT | |
| predicate | TEXT | |
| object_raw | TEXT | |
| value_num | REAL NULL | |
| unit | TEXT NULL | |
| unit_norm | TEXT NULL | |
| period | TEXT NULL | |
| period_norm | TEXT NULL | ISO-ish interval if parsed |
| scope | TEXT NULL | |
| as_of | TEXT NULL | |
| confidence | REAL | 0–1 |
| extra_json | JSON | evolving schema |
| quote | TEXT | |
| quote_ok | BOOLEAN | must be true to display |
| extractor_version | TEXT | prompt/schema version |

Indexes: `(document_id)`, `(subject)`, `(period_norm)`, `(predicate)`.

### embeddings

| Column | Type | Notes |
|---|---|---|
| fact_id | PK/FK | |
| model | TEXT | |
| dim | INT | |
| vector | BLOB | float32 |

### relations

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| fact_a_id | FK | store min(uuid) as a for uniqueness |
| fact_b_id | FK | |
| type | ENUM | corroborates, contradicts, reconciled, unrelated (unrelated optional persist) |
| axis | ENUM NULL | time, units, scope, entity, definition |
| confidence | REAL | |
| explanation | TEXT | |
| judge_version | TEXT | |
| UNIQUE(fact_a_id, fact_b_id) | | |

### cases

| Column | Type | Notes |
|---|---|---|
| slot | INT PK | 1–4 |
| relation_id | FK NULL | slots 1–3 |
| failure_id | FK NULL | slot 4 |
| title | TEXT | |
| curator_note | TEXT | human, committed in sample data |

### failures

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| document_id | FK NULL | |
| stage | TEXT | extract, verify, judge |
| payload_json | JSON | model output / chunk id |
| human_note | TEXT | |

### jobs

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| document_id | FK | |
| stage | TEXT | |
| status | TEXT | queued, running, done, error |
| attempts | INT | |
| error | TEXT NULL | |

## 4. Extractor schema (LLM)

Pydantic model `ExtractedFact` (list wrapped in `ExtractedPage`):

- `statement: str`
- `subject: str`
- `predicate: str`
- `object_raw: str`
- `value_num: float | None`
- `unit: str | None`
- `period: str | None`
- `scope: str | None`
- `quote: str`
- `confidence: float`

Prompt rules:

- Only facts supported by the page.
- `quote` must be copied verbatim from the page text provided in the prompt.
- Skip TOC, headers, legal boilerplate unless they contain a real claim.
- Prefer metrics, dates, entity roles, definitions.

## 5. Quote verification algorithm

```
function verify(quote, page_text) -> bool:
    q = collapse_ws(quote)
    t = collapse_ws(page_text)
    if q and q in t: return true
    if fuzzy_ratio(q, t) >= 0.95 and len(q) >= 20: return true  # optional
    return false
```

On false: insert `failures` (`stage=verify`); do not insert `facts`.

## 6. Normalization (keep raw)

| Raw | Norm approach |
|---|---|
| FY 2023-24, FY24, fiscal 2024 | `period_norm` like `FY2024` (India FY ending Mar) when pattern matches; else keep raw |
| ?1,234 crore, Rs. 1234 Cr | `unit_norm=INR`, `value_num` in crore **or** store `value_si` only if conversion is explicit |
| million / mn | same metric family |
| Company legal vs brand name | alias table built from repeated subjects, not a Delhivery list |

Never overwrite `object_raw`.

## 7. Blocking and judge

**Block** pair `(i,j)` if:

- `i.id < j.id`
- cosine(embed(subject+predicate+period), …) ? `?` (start 0.78) **OR**
- same `predicate` token set and overlapping `period_norm`

Skip: identical `quote`; both facts same `page_id` and same `value_num`.

**Judge prompt order (must):**

1. Same entity?  
2. Same metric/predicate?  
3. Same period?  
4. Same scope / definition / units?  
5. Then label:

| Label | When |
|---|---|
| unrelated | different entity or metric |
| corroborates | same claim, compatible values (incl. rounding / wording) |
| contradicts | same entity, metric, period, scope; incompatible values |
| reconciled | would look like contradict except axis differs |

Persist `explanation` in 2–5 sentences referencing both quotes.

## 8. REST LLD

Base path: `/api/v1`

| Method | Path | Request | Response | Errors |
|---|---|---|---|---|
| POST | `/documents` | `multipart/form-data` file | `201 {id, sha256, reused}` | 415, 413 |
| POST | `/documents/{id}/ingest` | empty | `202 {job_id}` | 404, 409 if running |
| GET | `/documents/{id}` | — | status, counts | 404 |
| GET | `/facts` | query: document_id, q, cursor, limit | `{items, next_cursor}` | 400 |
| GET | `/facts/{id}` | — | fact + evidence | 404 |
| GET | `/relations` | type | list | 400 |
| GET | `/relations/{id}` | — | pair + explanation | 404 |
| GET | `/cases` | — | four slots | — |
| GET | `/failures` | — | list | — |

**Error body:**

```json
{ "error": { "code": "QUOTE_MISMATCH", "message": "...", "details": {} } }
```

Codes: `VALIDATION`, `UNSUPPORTED_MEDIA`, `PAYLOAD_TOO_LARGE`, `PARSE_FAILED`, `QUOTE_MISMATCH`, `LLM_UNAVAILABLE`, `NOT_FOUND`, `CONFLICT`, `INGEST_RUNNING`.

Pagination: opaque cursor (created_at + id). Default limit 50, max 200.

Idempotency: POST `/documents` returns `reused: true` when `sha256` exists.

## 9. Pipeline sequence (happy path)

1. Save file to `data/uploads/{sha256}.pdf`.  
2. Insert `documents` (`uploaded`).  
3. Parse all pages in one transaction ? `parsed`.  
4. For each batch of K pages (K=3 default): LLM extract ? verify ? insert facts.  
5. Normalize new facts.  
6. Embed new facts.  
7. Block new facts against **all** facts (incremental).  
8. Judge new pairs.  
9. `ready`. UI polls GET document every 1s until ready/failed.

## 10. Concurrency

- Semaphore `LLM_CONCURRENCY=3`.
- One active ingest per `document_id` (`409 INGEST_RUNNING`).
- SQLite WAL; short transactions; do not hold a write lock during LLM HTTP.

## 11. Frontend LLD (if React)

- `api.ts` typed fetch wrappers.
- Pages match [IA](./IA.md) routes (React Router).
- Poll ingest with `setInterval` cleared on ready/failed.
- No global store; document/fact loaded per route.

## 12. Testing (LLD)

| Test | Asserts |
|---|---|
| `test_verify_quote` | substring and whitespace collapse |
| `test_contradict_gate` | different periods ? not contradicts |
| `test_ingest_pdf_header` | page_count ? 1 on sample PDF |
| `test_reuse_hash` | second POST same bytes reused |
| Fixture JSON | judge prompt snapshots optional |

Golden PDFs: one page from Delhivery AR checked into tests if license allows (assignment excerpts).

## 13. Pinning the four cases

After a successful Delhivery run, a script or admin POST (or SQL seed) writes `cases` rows with real `relation_id`s. Seed file `data/samples/cases.json` is committed so reviewers without LLM still see the gallery if they load samples.

## 14. Config

| Env | Meaning |
|---|---|
| `LLM_API_KEY` | required for live ingest |
| `LLM_MODEL` | extract model |
| `JUDGE_MODEL` | can be cheaper/faster |
| `EMBED_MODEL` | |
| `MAX_UPLOAD_MB` | default 25 |
| `BATCH_PAGES` | default 3 |
| `BLOCK_THRESHOLD` | default 0.78 |
