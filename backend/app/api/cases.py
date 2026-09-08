from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.relations import _rel_out
from app.db.orm import Case, Failure
from app.db.session import get_db

router = APIRouter(prefix="/cases", tags=["cases"])


@router.get("")
def list_cases(db: Session = Depends(get_db)):
    rows = db.scalars(select(Case).order_by(Case.slot)).all()
    if not rows:
        return {
            "items": [
                {
                    "slot": i,
                    "title": title,
                    "curator_note": "",
                    "relation": None,
                    "failure": None,
                }
                for i, title in enumerate(
                    [
                        "Corroborated across documents",
                        "Genuine or likely contradiction",
                        "Apparent contradiction explained by context",
                        "Extraction or reasoning failure",
                    ],
                    start=1,
                )
            ]
        }
    items = []
    for c in rows:
        rel = None
        if c.relation_id:
            from app.db.orm import Relation

            r = db.get(Relation, c.relation_id)
            rel = _rel_out(db, r) if r else None
        fail = db.get(Failure, c.failure_id) if c.failure_id else None
        items.append(
            {
                "slot": c.slot,
                "title": c.title,
                "curator_note": c.curator_note,
                "relation": rel,
                "failure": (
                    {
                        "id": fail.id,
                        "stage": fail.stage,
                        "human_note": fail.human_note,
                        "payload_json": fail.payload_json,
                    }
                    if fail
                    else None
                ),
            }
        )
    return {"items": items}
