# PRD — FactLayer

**Product:** FactLayer  
**Document type:** Product Requirements Document  
**Audience:** Candidate + Superjoin hiring reviewers  
**Related:** [MRD](./MRD.md) · [BRD](./BRD.md) · [MVP](./MVP.md) · [IA](./IA.md)

## 1. Summary

FactLayer is an inspector for **grounded facts** extracted from PDFs. Users upload documents; the system stores comparable claims (numeric and semantic), each tied to a **verbatim quote and page**, then **judges** pairs of claims as corroborating, contradicting, or reconcilable by context (time, scope, units, definition).

It is not a chatbot, not a knowledge-graph demo, and not a Delhivery-specific parser.

## 2. Problem

Facts in filings and institutional reports are scattered, restated, rounded, scoped differently, or silently changed. An extracted number without provenance is unusable in finance workflows. Two numbers that look like a conflict are often different periods or bases.

## 3. Goals and non-goals

### Goals

- Extract useful facts from arbitrary PDFs (starter set plus unseen files).
- Ground every displayed fact in source evidence.
- Explain cross-document agreement, conflict, and context.
- Be runnable from a README by a reviewer in minutes.

### Non-goals

- Production multi-tenant SaaS, authentication, SLAs.
- Chat / RAG as the primary UX.
- Graph database as the source of truth.
- OCR-first processing of scanned books.
- Writing back into Excel/Sheets (Superjoin product vision, not this intern slice).
- Perfect extraction.

## 4. Personas

| Persona | Job to be done | Success |
|---|---|---|
| Hiring evaluator | Upload PDFs, inspect facts and four required cases | Clear UI/API, no hardcoded filenames |
| Candidate / operator | Debug pipeline, pin demo cases, log failures | Failures visible |
| Future analyst (vision only) | Trust a figure before it enters a model | Click-through to page quote |

## 5. Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| F1 | Upload PDFs via UI and API | P0 |
| F2 | Parse pages and tables with stable locators | P0 |
| F3 | Extract numerical and semantic facts | P0 |
| F4 | Every stored fact has quote, page, document id | P0 |
| F5 | Normalize period, unit, entity without domain hardcoding | P0 |
| F6 | Label pairs: corroborates / contradicts / reconciled | P0 |
| F7 | Persist and show judge reasoning | P0 |
| F8 | Four-case gallery from real run data | P0 |
| F9 | Failure log for extraction/reasoning misses | P0 |
| F10 | Same pipeline on unseen PDFs | P0 |
| F11 | Idempotent re-ingest by content hash | P1 |
| F12 | Page-batched processing for large PDFs | P1 |
| F13 | Evolving attributes via JSON `extra` | P1 |

## 6. Non-functional requirements

| ID | Requirement |
|---|---|
| N1 | Single-machine, SQLite, README-runnable |
| N2 | Secrets never in git; sample JSON if LLM is paid |
| N3 | Precision over recall |
| N4 | Demo path ? 3 minutes: upload ? fact ? four cases |
| N5 | No `if filename == …` business logic |

## 7. UX principles

1. Evidence pane is mandatory wherever a fact is shown.
2. Relation views are side-by-side quotes plus a reason, not a graph first.
3. Cases and Failures are first-class nav items (evaluators look here first).
4. Status of ingest is visible (parsed / extracting / ready / failed).

## 8. Launch checklist (product)

- [ ] New PDF upload works
- [ ] Facts show quote + page
- [ ] Relations of three types exist
- [ ] Four cases demonstrated
- [ ] One failure documented
- [ ] Video ? 3 minutes
- [ ] README sections complete
