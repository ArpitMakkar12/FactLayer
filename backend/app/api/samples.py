from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

from app.api.errors import error
from app.db.session import SessionLocal
from app.jobs.samples import dump_layer, load_layer
from app.settings import ROOT

router = APIRouter(prefix="/samples", tags=["samples"])
SAMPLE_PATH = ROOT / "data" / "samples" / "layer.json"


@router.post("/load")
def load_samples():
    if not SAMPLE_PATH.exists():
        raise HTTPException(404, error("NOT_FOUND", "No committed sample dump at data/samples/layer.json"))
    db: Session = SessionLocal()
    try:
        counts = load_layer(db, SAMPLE_PATH)
        db.commit()
        return {"ok": True, "path": str(SAMPLE_PATH), **counts}
    except Exception as exc:
        db.rollback()
        raise HTTPException(400, error("VALIDATION", str(exc)[:500])) from exc
    finally:
        db.close()


@router.post("/dump")
def dump_samples():
    SAMPLE_PATH.parent.mkdir(parents=True, exist_ok=True)
    db: Session = SessionLocal()
    try:
        dump_layer(db, SAMPLE_PATH)
        return {"ok": True, "path": str(SAMPLE_PATH)}
    finally:
        db.close()
