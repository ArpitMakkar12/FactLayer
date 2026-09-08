# BRD — FactLayer

**Document type:** Business Requirements Document  
**Business context:** Superjoin VIT 2026 engineering intern hiring assignment.

## 1. Business objective

**For Superjoin:** Identify candidates who can explore an unfamiliar document-AI problem, make engineering trade-offs, and ship a small system whose behavior is inspectable.

**For the candidate:** Produce a GitHub repository and ?3 minute demo that prove product sense, grounding discipline, and honesty about failures.

## 2. Stakeholders

| Stakeholder | Interest |
|---|---|
| Hiring engineers | Runnable project, readable architecture, real trade-offs |
| Candidate | Finishable scope, clear P0 vs P1 |
| Implied future PM | Prototype maps to extraction + lineage (Superjoin finance AI) |

## 3. Business rules

| ID | Rule |
|---|---|
| B1 | No fact is stored or shown without a source span that verifies against page text |
| B2 | `reconciled` relations must include an axis: time, units, scope, entity, or definition |
| B3 | `contradicts` requires same metric **and** overlapping period **and** comparable scope; otherwise it is reconciled or unrelated |
| B4 | Identical PDF bytes (SHA-256) must not rebuild knowledge if status is `ready` (P1; strongly preferred) |
| B5 | LLM cost is bounded: page batches + candidate blocking (not N² pairwise LLM) |
| B6 | The four demo cases are **data** (pinned IDs), not code branches on filenames |
| B7 | Credentials never enter git; paid APIs must have committed sample output |

## 4. Scope boundaries

**In:** PDF upload, fact extraction, evidence, cross-document relations, inspector UI or API, README, video, sample outputs.

**Out:** Multi-tenant billing, SSO, production monitoring, Excel plugin, Kubernetes, training custom models.

## 5. Success metrics (assignment KPIs)

| Metric | Target |
|---|---|
| Time to first grounded fact after setup | < 3 minutes of evaluator clicking |
| Grounding coverage of displayed facts | 100% quote + page |
| Required cases | 4 / 4 |
| Generalization | ?1 PDF not in the hardcoded sense (unseen file) |
| Honesty | ?1 logged failure with a proposed improvement |
| Demo length | ? 3 minutes |

## 6. Constraints

- Any language/stack allowed; reviewers must be able to run it.
- Open-ended by design; a smaller clear prototype beats a large opaque one.
- Starter datasets: Delhivery (3) and India macroeconomy (3); demo on one corpus, smoke-test the other.

## 7. Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| LLM hallucinated numbers | Trust failure | Quote verification; drop on mismatch |
| Fact spam | Unreadable relations | Precision filter; confidence threshold |
| Pairwise LLM cost | Slow / expensive | Embedding block |
| Incomplete starter PDFs | Cannot show four cases | Restore full 3-file Delhivery set |
| Reviewer has no API key | Cannot run live | `data/samples/` + video |

## 8. Compliance / hygiene

- Public PDFs only (assignment starter set).
- No scraping behind logins.
- No secrets, no customer data.
