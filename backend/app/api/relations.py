from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.errors import error
from app.api.facts import _fact_out
from app.db.orm import Fact, Relation
from app.db.session import get_db

router = APIRouter(prefix="/relations", tags=["relations"])


def _rel_out(db: Session, rel: Relation) -> dict:
    a = db.get(Fact, rel.fact_a_id)
    b = db.get(Fact, rel.fact_b_id)
    return {
        "id": rel.id,
        "type": rel.type,
        "axis": rel.axis,
        "confidence": rel.confidence,
        "explanation": rel.explanation,
        "judge_version": rel.judge_version,
        "fact_a": _fact_out(db, a) if a else None,
        "fact_b": _fact_out(db, b) if b else None,
    }


@router.get("")
def list_relations(
    type: str | None = Query(None, alias="type"),
    q: str | None = Query(None),
    limit: int = Query(20, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    from sqlalchemy import func, or_

    stmt = select(Relation).order_by(Relation.confidence.desc())
    count_stmt = select(func.count()).select_from(Relation)
    if type:
        stmt = stmt.where(Relation.type == type)
        count_stmt = count_stmt.where(Relation.type == type)
    if q:
        like = f"%{q}%"
        # Search in explanation or in linked facts' statements
        matching_fact_ids = select(Fact.id).where(Fact.statement.ilike(like))
        search_cond = or_(
            Relation.explanation.ilike(like),
            Relation.fact_a_id.in_(matching_fact_ids),
            Relation.fact_b_id.in_(matching_fact_ids),
        )
        stmt = stmt.where(search_cond)
        count_stmt = count_stmt.where(search_cond)
    total = db.scalar(count_stmt) or 0
    rows = db.scalars(stmt.offset(offset).limit(limit)).all()
    return {
        "items": [_rel_out(db, r) for r in rows],
        "total": total,
        "offset": offset,
        "limit": limit,
        "has_more": offset + len(rows) < total,
    }


@router.get("/{relation_id}")
def get_relation(relation_id: str, db: Session = Depends(get_db)):
    rel = db.get(Relation, relation_id)
    if not rel:
        raise HTTPException(404, error("NOT_FOUND", "Relation not found"))
    return _rel_out(db, rel)
