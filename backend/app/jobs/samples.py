from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.orm import Case, Document, Embedding, Fact, Failure, Page, Relation
from app.jobs.pipeline import pin_cases


def dump_layer(db: Session, path: Path) -> None:
    payload = {
        "documents": [
            {
                "id": d.id,
                "filename": d.filename,
                "sha256": d.sha256,
                "status": d.status,
                "page_count": d.page_count,
            }
            for d in db.scalars(select(Document)).all()
        ],
        "pages": [
            {"id": p.id, "document_id": p.document_id, "page_no": p.page_no, "text": p.text[:8000]}
            for p in db.scalars(select(Page)).all()
        ],
        "facts": [_fact_row(f) for f in db.scalars(select(Fact)).all()],
        "embeddings": [
            {"fact_id": e.fact_id, "model": e.model, "tokens_json": e.tokens_json}
            for e in db.scalars(select(Embedding)).all()
        ],
        "relations": [
            {
                "id": r.id,
                "fact_a_id": r.fact_a_id,
                "fact_b_id": r.fact_b_id,
                "type": r.type,
                "axis": r.axis,
                "confidence": r.confidence,
                "explanation": r.explanation,
                "judge_version": r.judge_version,
            }
            for r in db.scalars(select(Relation)).all()
        ],
        "failures": [
            {
                "id": f.id,
                "document_id": f.document_id,
                "stage": f.stage,
                "payload_json": f.payload_json,
                "human_note": f.human_note,
            }
            for f in db.scalars(select(Failure)).all()
        ],
        "cases": [
            {
                "slot": c.slot,
                "relation_id": c.relation_id,
                "failure_id": c.failure_id,
                "title": c.title,
                "curator_note": c.curator_note,
            }
            for c in db.scalars(select(Case)).all()
        ],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _fact_row(f: Fact) -> dict:
    return {
        "id": f.id,
        "document_id": f.document_id,
        "page_id": f.page_id,
        "statement": f.statement,
        "subject": f.subject,
        "predicate": f.predicate,
        "object_raw": f.object_raw,
        "value_num": f.value_num,
        "unit": f.unit,
        "unit_norm": f.unit_norm,
        "period": f.period,
        "period_norm": f.period_norm,
        "scope": f.scope,
        "confidence": f.confidence,
        "extra_json": f.extra_json,
        "quote": f.quote,
        "quote_ok": f.quote_ok,
        "extractor_version": f.extractor_version,
    }


def load_layer(db: Session, path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    existing_docs = {d.sha256 for d in db.scalars(select(Document)).all()}
    doc_map = {d.id: d for d in db.scalars(select(Document)).all()}
    loaded_docs = 0
    for row in data.get("documents") or []:
        if row["sha256"] in existing_docs:
            continue
        db.merge(
            Document(
                id=row["id"],
                filename=row["filename"],
                sha256=row["sha256"],
                status=row.get("status") or "ready",
                page_count=row.get("page_count") or 0,
            )
        )
        existing_docs.add(row["sha256"])
        loaded_docs += 1
        doc_map[row["id"]] = True
    page_ids = {p.id for p in db.scalars(select(Page)).all()}
    for row in data.get("pages") or []:
        if row["id"] in page_ids:
            continue
        if not db.get(Document, row["document_id"]):
            continue
        db.add(Page(**row))
        page_ids.add(row["id"])
    fact_ids = {f.id for f in db.scalars(select(Fact)).all()}
    for row in data.get("facts") or []:
        if row["id"] in fact_ids:
            continue
        if not db.get(Document, row["document_id"]):
            continue
        db.add(Fact(**row))
        fact_ids.add(row["id"])
    emb_ids = {e.fact_id for e in db.scalars(select(Embedding)).all()}
    for row in data.get("embeddings") or []:
        if row["fact_id"] in emb_ids or row["fact_id"] not in fact_ids:
            continue
        db.add(Embedding(**row))
    rel_ids = {r.id for r in db.scalars(select(Relation)).all()}
    for row in data.get("relations") or []:
        if row["id"] in rel_ids:
            continue
        if row["fact_a_id"] not in fact_ids or row["fact_b_id"] not in fact_ids:
            continue
        db.add(Relation(**row))
        rel_ids.add(row["id"])
    fail_ids = {f.id for f in db.scalars(select(Failure)).all()}
    for row in data.get("failures") or []:
        if row["id"] in fail_ids:
            continue
        db.add(Failure(**row))
        fail_ids.add(row["id"])
    db.flush()
    pin_cases(db)
    return {
        "documents_loaded": loaded_docs,
        "facts": len(fact_ids),
        "relations": len(rel_ids),
    }
