# MRD — FactLayer

**Document type:** Market Requirements Document  
**Note:** This intern assignment is not a GTM launch. The MRD frames **why the problem exists in Superjoin’s market** so engineering choices stay product-shaped.

## 1. Market problem

Finance teams still pull assumptions from PDFs (annual reports, prospectuses, earnings decks, survey chapters) into spreadsheets. The expensive part is not “summarize this PDF.” It is:

- finding the **number that belongs in a model**;
- knowing **which period and scope** it uses;
- seeing whether **another document agrees**.

Generic document Q&A does not produce **rows** that can be compared. Classic knowledge graphs often skip **grounding and explanation**.

## 2. Who cares

| Segment | Pain | Why Superjoin-adjacent |
|---|---|---|
| IB / PE / FDD analysts | Data rooms, CIMs, filings, conflicting figures | Superjoin’s Excel agent story: extract + audit |
| FP&A / IR | MIS vs published reports | Same metric, different definitions |
| Intern evaluator (immediate “market”) | Need to see thinking, not a toy graph | Hiring assignment |

## 3. Jobs to be done (market)

1. **Extract** a claim as a structured object (metric, value, unit, period, scope).
2. **Ground** it so a senior can challenge the intern/analyst.
3. **Reconcile** two claims that look inconsistent.
4. **Flag** true conflicts instead of averaging them away.

## 4. Competitive frame

| Approach | Typical gap |
|---|---|
| PDF chat assistants | No first-class fact objects; weak conflict detection |
| NER + Neo4j | Graph theatre; poor quote-level grounding |
| Table-only extractors | Miss semantic facts (directors, definitions, caveats) |
| Manual Excel | Slow; this is the workflow Superjoin automates later |

## 5. Market requirements ? intern slice

| Market need | Requirement on this repo |
|---|---|
| Audit trail | Quote + page on every fact |
| Period / scope discipline | Relation `axis` when reconciled |
| Next filing must work | No document-specific schema or filenames |
| Inspect, don’t just prompt | UI/API over facts and relations, not a chat home |
| Honesty under uncertainty | Explicit failure objects |

## 6. Positioning

**FactLayer is the middle layer between messy PDFs and a spreadsheet: structured, comparable, evidenced claims.**

A later Superjoin product could write these facts into Sheets/Excel with formulas. That writeback is **out of scope** for the intern MVP; the **shape of the objects** should still look like something a spreadsheet could ingest.

## 7. Open market questions (not blocking MVP)

- How should crore/lakh/million normalization work globally?
- Should footnotes override table cells?
- What’s the right default when two official bodies publish different vintages of GDP?

These belong in Limitations, not in frozen code.
