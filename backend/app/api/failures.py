from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.errors import error
from app.db.orm import Document, Failure
from app.db.session import get_db

router = APIRouter(prefix="/failures", tags=["failures"])


def _fail_out(db: Session, f: Failure) -> dict:
    doc = db.get(Document, f.document_id) if f.document_id else None
    return {
        "id": f.id,
        "document_id": f.document_id,
        "document_filename": doc.filename if doc else None,
        "stage": f.stage,
        "human_note": f.human_note,
        "payload_json": f.payload_json,
        "created_at": f.created_at.isoformat() if f.created_at else None,
    }


@router.get("")
def list_failures(
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    from sqlalchemy import func, or_

    stmt = select(Failure).order_by(Failure.created_at.desc())
    count_stmt = select(func.count()).select_from(Failure)

    if q:
        like = f"%{q}%"
        search_cond = or_(
            Failure.human_note.ilike(like),
            Failure.payload_json.ilike(like),
            Failure.stage.ilike(like)
        )
        stmt = stmt.where(search_cond)
        count_stmt = count_stmt.where(search_cond)

    total = db.scalar(count_stmt) or 0
    rows = db.scalars(stmt.offset(offset).limit(limit)).all()

    return {
        "items": [_fail_out(db, f) for f in rows],
        "total": total,
        "offset": offset,
        "limit": limit,
        "has_more": offset + len(rows) < total,
    }


@router.get("/{failure_id}")
def get_failure(failure_id: str, db: Session = Depends(get_db)):
    f = db.get(Failure, failure_id)
    if not f:
        raise HTTPException(404, error("NOT_FOUND", "Failure not found"))
    return _fail_out(db, f)
