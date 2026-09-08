# IA — FactLayer information architecture

**Document type:** Information architecture  
**UX metaphor:** An **inspector** (like a debugger for claims), not a search chat.

## 1. Mental model

```
Workspace
  ??? Document (file, hash, status)
        ??? Pages (text, tables)
        ??? Facts (claim + evidence)
              ??? Relations (pair of facts + judgment)

Curated views (not separate data models):
  ??? Cases (pinned relations / failure)
  ??? Failures (pipeline misses)
```

## 2. Core objects

| Object | Meaning | User-visible fields |
|---|---|---|
| Document | One PDF | name, page count, status, fact count |
| Page | Locator | page number, snippet |
| Fact | One claim | statement, subject, metric, value, unit, period, scope, confidence |
| Evidence | Grounding | quote, page, document |
| Relation | Comparison | type, axis, explanation, two facts |
| Case | Demo pin | slot 1–4, pointer to relation or failure |
| Failure | Honest miss | stage, snippet, note |

## 3. Navigation sitemap

| Route | Purpose | Primary objects |
|---|---|---|
| `/` | Upload + recent documents | Document |
| `/documents/:id` | Ingest status, counts | Document, Fact counts |
| `/facts` | Browse / filter | Fact |
| `/facts/:id` | Detail + evidence + links | Fact, Relation |
| `/relations` | Browse by type | Relation |
| `/relations/:id` | Side-by-side evidence | Relation, Fact ×2 |
| `/cases` | Assignment four cases | Case |
| `/failures` | Case 4 and other misses | Failure |

**Not a nav item:** Chat, Graph, Settings (beyond a local `.env`).

## 4. Page layouts

### Home

- Dropzone (PDF)
- List of documents with status pills: uploaded / parsed / extracting / ready / failed

### Fact list

- Filters: document, has_value, min confidence, text search
- Row: statement, period, document, confidence
- Selecting a row opens evidence pane (split view)

### Fact detail

- Header: statement
- Attributes grid: subject, predicate, value, unit, period, scope
- Evidence card: quote, page, filename
- Related relations list

### Relation detail

- Two columns of evidence
- Center/bottom: type, axis, explanation, confidence

### Cases

- Four stacked case cards, each with type label, both quotes, explanation
- Case 4 may point at `/failures/:id`

## 5. Label language (IA copy)

Use these words consistently in UI and API:

- **Fact** not “triple” or “entity”
- **Evidence** not “chunk”
- **Reconciled** not “maybe conflict”
- **Axis** for why it reconciled (time / units / scope / entity / definition)
- **Failure** not “error toast” only — persisted object

## 6. Empty and error states

| State | Copy intent |
|---|---|
| No documents | Prompt upload; do not show fake facts |
| Ingest in progress | Polling status, not a spinner with no stage |
| No relations yet | Explain that a second PDF or more facts are needed |
| Quote verify failed | Land in Failures, not silent drop with no trace |

## 7. API as information architecture

REST resources match the sitemap: `documents`, `facts`, `relations`, `cases`, `failures`. No RPC named `/ask` in MVP.
