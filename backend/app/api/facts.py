import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.errors import error
from app.db.orm import Document, Fact, Page
from app.db.session import get_db

router = APIRouter(prefix="/facts", tags=["facts"])


def _fact_out(db: Session, fact: Fact) -> dict:
    page = db.get(Page, fact.page_id)
    doc = db.get(Document, fact.document_id)
    try:
        extra = json.loads(fact.extra_json or "{}")
    except json.JSONDecodeError:
        extra = {}
    return {
        "id": fact.id,
        "document_id": fact.document_id,
        "document_filename": doc.filename if doc else None,
        "page": page.page_no if page else None,
        "statement": fact.statement,
        "subject": fact.subject,
        "predicate": fact.predicate,
        "object_raw": fact.object_raw,
        "value_num": fact.value_num,
        "unit": fact.unit,
        "unit_norm": fact.unit_norm,
        "period": fact.period,
        "period_norm": fact.period_norm,
        "scope": fact.scope,
        "as_of": fact.as_of,
        "confidence": fact.confidence,
        "extra": extra,
        "quote": fact.quote,
        "quote_ok": fact.quote_ok,
        "extractor_version": fact.extractor_version,
    }


@router.get("")
def list_facts(
    document_id: str | None = None,
    q: str | None = None,
    has_value: bool | None = None,
    min_confidence: float | None = Query(None, ge=0, le=1),
    limit: int = Query(50, le=200),
    cursor: int = Query(0, ge=0, alias="cursor"),
    db: Session = Depends(get_db),
):
    stmt = select(Fact).where(Fact.quote_ok.is_(True)).order_by(Fact.confidence.desc())
    if document_id:
        stmt = stmt.where(Fact.document_id == document_id)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(Fact.statement.ilike(like) | Fact.predicate.ilike(like))
    if has_value:
        stmt = stmt.where(Fact.value_num.is_not(None))
    if min_confidence is not None:
        stmt = stmt.where(Fact.confidence >= min_confidence)
    rows = db.scalars(stmt.offset(cursor).limit(limit)).all()
    next_cursor = cursor + len(rows) if len(rows) == limit else None
    return {"items": [_fact_out(db, f) for f in rows], "next_cursor": next_cursor}


@router.get("/{fact_id}")
def get_fact(fact_id: str, db: Session = Depends(get_db)):
    fact = db.get(Fact, fact_id)
    if not fact or not fact.quote_ok:
        raise HTTPException(404, error("NOT_FOUND", "Fact not found"))
    return _fact_out(db, fact)
