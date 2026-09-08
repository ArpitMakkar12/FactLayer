# Implementation plan — FactLayer MVP + brownie

Companion canvas: Cursor `factlayer-implementation-plan.canvas.tsx`.

**Rule:** schema is incremental from day one (`sha256`, `extra_json`, global facts). Brownie is proven in Phase 8, not redesigned there.

## Principle

1. First green slice: one page ? verified fact ? `GET /facts/{id}`.
2. No UI until quote verification works.
3. No Delhivery/India special cases in `app/`.
4. Commit at every phase gate (meaningful git).

## Phases

| Phase | Focus | Exit criterion |
|---|---|---|
| 0 | Repo, LLD schema, health | Tables exist; `GET /health` |
| 1 | PDF ingest, hash, skip empty pages | 100-page excerpt parses quickly; reuse by SHA-256 |
| 2 | LLM extract + quote verify + failures | Grounded facts only; fixture failure logged |
| 3 | Normalize + embed | Shared `period_norm`; vectors stored |
| 4 | Block + judge, pairs involving **new** facts only | Fixture: corroborates + reconciled; different period ? contradict |
| 5 | REST `/api/v1` | curl-only demo of upload ? facts ? relations |
| 6 | Inspector (`/cases`, `/failures`, evidence pane) | Demo script without curl |
| 7 | Delhivery 3 PDFs; pin cases; India smoke | Four slots + held-out PDF facts |
| 8 | Brownie proofs | Timing, multi-doc layer, extra JSON, incremental no-op |
| 9 | Samples, README, video, GitHub, form | Assignment checklist true |

## Task parameter coverage

| Assignment ask | Phase |
|---|---|
| Extract numerical/semantic facts | 2 |
| Evidence (quote, page, doc) | 2, 6 |
| Corroborate / contradict / reconcile | 4 |
| API or UI upload | 5–6 |
| No hardcoded facts/filenames/schemas | 0, 7 (G7) |
| Four cases + reasoning | 7, 6 |
| Git + README four sections + ?3 min video | 9 |

## Brownie (hooks vs proof)

| Brownie | Built in | Proven in |
|---|---|---|
| Large PDFs | 1–2 page batches, skip empty, job+poll | 8 timing on ~100 pages |
| Many PDFs, one layer | 0 one DB; 4 compare vs all facts | 8 fourth PDF links to old facts |
| Evolving schema | 0 `extra_json`; 2 prompt | 8 UI shows unknown key |
| Incremental | 1 hash reuse; 4 new-fact pairs only | 8 re-POST skips LLM |

## Gates (do not skip)

- **G0** No company names in production code.
- **G2** `quote_ok` is always true for displayed facts.
- **G3** Judge cannot mark different periods as contradicts (fixture).
- **G7** India (or any new) PDF works with empty `git diff` in `app/`.
- **G8** README states all four brownie proofs.

## Video (3:00)

Upload ? fact evidence ? cases 1–3 ? failure ? 20s brownie (reuse or extra or 4th PDF).

## Before Phase 7

Restore full Delhivery starter set (3 PDFs) and at least one India-macroeconomy PDF.
