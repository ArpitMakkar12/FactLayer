from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.errors import error
from app.db.orm import Document, Fact, Job, Relation
from app.db.session import SessionLocal, get_db
from app.ingest.pdf import sha256_bytes
from app.jobs.pipeline import run_ingest
from app.settings import settings

router = APIRouter(prefix="/documents", tags=["documents"])


def _counts(db: Session, doc_id: str) -> dict:
    facts = db.scalar(select(func.count()).select_from(Fact).where(Fact.document_id == doc_id)) or 0
    rels = db.scalar(
        select(func.count())
        .select_from(Relation)
        .where(
            or_(
                Relation.fact_a_id.in_(select(Fact.id).where(Fact.document_id == doc_id)),
                Relation.fact_b_id.in_(select(Fact.id).where(Fact.document_id == doc_id)),
            )
        )
    ) or 0
    return {"fact_count": facts, "relation_count": rels}


def _latest_job(db: Session, doc_id: str) -> dict | None:
    job = db.scalar(select(Job).where(Job.document_id == doc_id).order_by(Job.created_at.desc()).limit(1))
    if not job:
        return None
    return {
        "id": job.id,
        "stage": job.stage,
        "status": job.status,
        "error": job.error,
        "attempts": job.attempts,
    }


def _doc_out(db: Session, doc: Document) -> dict:
    return {
        "id": doc.id,
        "filename": doc.filename,
        "sha256": doc.sha256,
        "status": doc.status,
        "collection": doc.collection,
        "page_count": doc.page_count,
        "error": doc.error,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
        "latest_job": _latest_job(db, doc.id),
        **_counts(db, doc.id),
    }


@router.get("")
def list_documents(db: Session = Depends(get_db)):
    rows = db.scalars(select(Document).order_by(Document.created_at.desc())).all()
    return {"items": [_doc_out(db, d) for d in rows]}


@router.get("/{document_id}")
def get_document(document_id: str, db: Session = Depends(get_db)):
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(404, error("NOT_FOUND", "Document not found"))
    return _doc_out(db, doc)


@router.post("")
async def upload_document(
    file: UploadFile = File(...),
    collection: str | None = Form(None),
    db: Session = Depends(get_db),
):
    raw = await file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(raw) > max_bytes:
        raise HTTPException(413, error("PAYLOAD_TOO_LARGE", f"Max {settings.max_upload_mb} MB"))
    if not raw.startswith(b"%PDF"):
        raise HTTPException(415, error("UNSUPPORTED_MEDIA", "Only PDF files are accepted"))
    digest = sha256_bytes(raw)
    existing = db.scalar(select(Document).where(Document.sha256 == digest))
    dest = Path(settings.upload_dir) / f"{digest}.pdf"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        dest.write_bytes(raw)
    name = Path(file.filename or "upload.pdf").name
    if existing:
        # Update collection if provided
        if collection and not existing.collection:
            existing.collection = collection
            db.commit()
        return JSONResponse(
            status_code=200,
            content={"id": existing.id, "sha256": digest, "reused": True, "status": existing.status},
        )
    doc = Document(filename=name, sha256=digest, status="uploaded", collection=collection or None)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return JSONResponse(
        status_code=201,
        content={"id": doc.id, "sha256": digest, "reused": False, "status": doc.status},
    )


@router.delete("/{document_id}")
def delete_document(document_id: str, db: Session = Depends(get_db)):
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(404, error("NOT_FOUND", "Document not found"))
    # Cascade deletes pages, facts, embeddings. Relations referencing these facts also cascade.
    db.delete(doc)
    db.commit()
    return {"deleted": True, "id": document_id}


def _run_job(document_id: str, pdf_path: str) -> None:
    db = SessionLocal()
    try:
        run_ingest(db, document_id, Path(pdf_path))
    finally:
        db.close()


@router.post("/{document_id}/ingest")
def ingest_document(document_id: str, background: BackgroundTasks, db: Session = Depends(get_db)):
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(404, error("NOT_FOUND", "Document not found"))
    if doc.status == "ready":
        return {
            "job_id": None,
            "status": doc.status,
            "skipped": True,
            "reason": "already ready (incremental)",
        }
    active = db.scalars(
        select(Job).where(
            Job.document_id == doc.id,
            Job.status.in_(("queued", "running")),
        )
    ).first()
    if active and doc.status == "uploaded":
        raise HTTPException(409, error("INGEST_RUNNING", "Ingest already running"))
    if active:
        active.status = "error"
        active.error = "superseded by retry"
    path = Path(settings.upload_dir) / f"{doc.sha256}.pdf"
    if not path.exists():
        raise HTTPException(404, error("NOT_FOUND", "PDF bytes missing on disk"))
    job = Job(document_id=doc.id, stage="ingest", status="queued", attempts=0)
    db.add(job)
    db.commit()
    db.refresh(job)
    background.add_task(_run_job, doc.id, str(path))
    return JSONResponse(status_code=202, content={"job_id": job.id, "status": "queued"})
