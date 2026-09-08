# HLD — FactLayer high-level design

**Document type:** High-level design  
**Style:** Modular monolith, single machine, LLM as an untrusted dependency.

## 1. Design thesis

A **fact** is a typed claim with provenance. A **relation** is a judged comparison with an explanation. Storage of those two objects is the system of record. Graphs, search, and chat are optional views.

## 2. Context diagram

```
[Evaluator browser]
        |  HTTP (REST + multipart)
        v
[FactLayer monolith: FastAPI]
        |-- filesystem: data/uploads/{sha256}.pdf
        |-- SQLite: facts, relations, jobs
        v
[LLM + embeddings provider]   (untrusted)
```

External systems: only the LLM/embedding API. No identity provider, no message bus, no graph DB.

## 3. Logical pipeline

```
Upload ? Parse ? Extract ? Verify quote ? Normalize ? Embed
                                                      ?
UI ? API ? Store ? Judge ? Block candidate pairs ?????
```

Persist after **Parse**, **Extract**, and **Judge** so a crash can resume.

## 4. Components

| Component | Responsibility | Explicitly not |
|---|---|---|
| Inspector UI | Upload, browse, cases, failures | Business logic |
| API | REST, job kickoff, pagination | Prompt strings |
| Ingest | PDF ? pages/tables | LLM |
| Extract | Chunks ? candidate JSON facts | Cross-doc compare |
| Verifier | Quote must appear in page text | “Trust the model” |
| Normalize | Canonical period/unit/entity aliases | Inventing values |
| Match | Candidate pairs (embeddings / overlap) | Final labels |
| Judge | Relation type + axis + explanation | Persisting ungrounded facts |
| Store | SQLite + files | PDF bytes in SQL |

## 5. Architecture decisions (ADRs, short)

### ADR-1: Modular monolith

- **Decision:** One Python process, packages by stage.
- **Rejected:** Microservices, Celery, Redis.
- **Why:** One developer, README run, assignment week.
- **Evolve:** Extract `ingest` / `judge` workers behind the same interfaces if latency requires it.

### ADR-2: SQLite as system of record

- **Decision:** SQLite WAL + JSON `extra` column.
- **Rejected:** Postgres (ops), Neo4j (graph is not the product).
- **Why:** Inspectable, portable, matches “prototype over platform.”

### ADR-3: REST, not GraphQL / not chat

- **Decision:** Resource APIs matching IA objects.
- **Why:** Evaluators curl; OpenAPI documents itself.

### ADR-4: Grounding gate

- **Decision:** Facts that fail quote verification are **failures**, not facts.
- **Why:** Hallucinated revenue is worse than a missed fact.

### ADR-5: Block then judge

- **Decision:** Cheap candidate generation, expensive LLM only on pairs.
- **Why:** N² LLM is cost and latency failure.

### ADR-6: Incremental knowledge layer

- **Decision:** New documents compare against **all existing facts**, not only within the same upload batch.
- **Why:** Brownie + actual “layer” semantics. P1 if time-boxed, but schema should allow it from day one.

## 6. Deployment view (MVP)

- Developer or reviewer machine.
- `uvicorn` + static frontend (`vite preview` or FastAPI `StaticFiles`).
- `.env` for `LLM_API_KEY`.
- Optional: Docker **one container** later; not required.

## 7. Trust and threat model (lightweight)

| Input | Trust | Control |
|---|---|---|
| PDF bytes | Untrusted | Size cap, PDF-only MIME, no exec |
| LLM JSON | Untrusted | Schema parse + quote verify |
| UI | Trusted local | No auth in MVP |
| Sample JSON in git | Trusted fixtures | For offline review |

Do not log raw API keys. Truncate page text in failure logs if needed.

## 8. Scalability (honest)

MVP target: tens of PDFs, ?100 pages each, hundreds to low thousands of facts.

Bottlenecks: LLM extract per page, LLM judge per pair.

Mitigations already in HLD: batching, blocking, hash short-circuit.

Not in MVP: horizontal workers, vector DB, multi-tenant isolation.

## 9. Observability

Minimum: structured logs per job stage; `jobs` and `failures` tables are the trace. No APM.

## 10. Mapping to assignment brownie

| Brownie | HLD hook |
|---|---|
| Large PDFs | Page-batch extract; skip near-empty pages |
| Many PDFs | Global fact index; incremental pair generation |
| Evolving schema | `facts.extra_json` |
| Incremental | Unique `documents.sha256`; judge only pairs involving new fact ids |
