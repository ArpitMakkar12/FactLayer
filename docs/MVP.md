# MVP — FactLayer

**Document type:** Minimum Viable Product definition  
**Bar:** Assignment “Before you submit” checklist.

## 1. One-sentence MVP

A local web app that accepts **new PDFs**, extracts **grounded facts**, computes **cross-document relations**, and shows **four required cases** (including a real failure) without document-specific hardcoding.

## 2. In / stretch / out

| P0 — must ship | P1 — brownie | Out |
|---|---|---|
| Upload PDF (UI + API) | Incremental ingest by SHA-256 | Auth, multi-user |
| Page parse + locators | Large PDF page batching | Neo4j / graph as core |
| Facts with quote + page | Dynamic `extra` attributes | Chat home |
| Normalize period/unit/entity lightly | Many PDFs in one layer (already implied if incremental) | Excel writeback |
| Relations: corroborates / contradicts / reconciled | — | OCR pipeline, K8s |
| Four-case gallery | — | Fine-tuning |
| Failure log | — | |
| README + video + sample JSON | — | |

## 3. User stories and acceptance

| Story | Acceptance |
|---|---|
| Upload a PDF | Document row with status `ready` or `failed` |
| Open a fact | Statement, value/period/scope if any, quote, page, document name |
| Filter relations | Type filter works; explanation visible |
| Open Cases | Four slots filled from a real run |
| Open Failures | At least one miss + “what we would improve” |
| Upload a different PDF | Facts appear with **no code change** |

## 4. Vertical slice (build this first)

One PDF page ? one verified fact in SQLite ? GET `/facts/{id}` ? UI card.

Do not start the React app until this slice is green.

## 5. Cut line if time slips

Keep: FastAPI, SQLite, quote verifier, judge, one HTML inspector, four-case page.

Drop: React, fancy filters, embeddings (replace with token overlap), second corpus in the video.

Never drop: evidence, relation explanations, case 4 honesty.

## 6. Demo script (MVP acceptance)

1. Upload (or re-open) a PDF  
2. Show one fact with quote  
3. Show corroboration, contradiction, reconciled  
4. Show failure  
5. Stop under 3:00
