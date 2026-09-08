from pathlib import Path

from sqlalchemy import select

from app.db.orm import Document, Fact, Failure, Relation
from app.ingest.pdf import parse_pdf, sha256_bytes
from app.jobs.pipeline import run_ingest


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True
    r2 = client.get("/api/v1/health")
    assert r2.status_code == 200


def test_reuse_hash(client, tiny_pdf):
    with tiny_pdf.open("rb") as f:
        r1 = client.post("/api/v1/documents", files={"file": ("tiny.pdf", f, "application/pdf")})
    assert r1.status_code == 201
    body1 = r1.json()
    assert body1["reused"] is False
    with tiny_pdf.open("rb") as f:
        r2 = client.post("/api/v1/documents", files={"file": ("tiny.pdf", f, "application/pdf")})
    assert r2.status_code == 200
    body2 = r2.json()
    assert body2["reused"] is True
    assert body2["id"] == body1["id"]
    assert body2["sha256"] == sha256_bytes(tiny_pdf.read_bytes())


def test_reject_non_pdf(client, workdir):
    p = workdir / "x.txt"
    p.write_text("hello")
    with p.open("rb") as f:
        r = client.post("/api/v1/documents", files={"file": ("x.txt", f, "text/plain")})
    assert r.status_code == 415
    assert r.json()["error"]["code"] == "UNSUPPORTED_MEDIA"


def test_ingest_pdf_header(tiny_pdf):
    pages, count = parse_pdf(tiny_pdf)
    assert count >= 1
    assert pages[0]["page_no"] == 1
    assert "revenue" in pages[0]["text"].lower()


def test_ingest_and_relations(db_session, sample_pdfs, monkeypatch, workdir):
    from app.settings import settings

    monkeypatch.setattr(settings, "upload_dir", str(workdir / "uploads"))
    a, b = sample_pdfs
    for path in (a, b):
        digest = sha256_bytes(path.read_bytes())
        dest = Path(settings.upload_dir) / f"{digest}.pdf"
        dest.write_bytes(path.read_bytes())
        doc = Document(filename=path.name, sha256=digest, status="uploaded")
        db_session.add(doc)
        db_session.commit()
        run_ingest(db_session, doc.id, dest)
        db_session.refresh(doc)
        assert doc.status == "ready"
        assert doc.page_count >= 1

    facts = list(db_session.scalars(select(Fact).where(Fact.quote_ok.is_(True))))
    assert facts
    assert all(f.quote_ok for f in facts)
    types = {r.type for r in db_session.scalars(select(Relation))}
    assert "corroborates" in types
    assert "reconciled" in types
    assert "contradicts" in types
    failures = list(db_session.scalars(select(Failure)))
    assert any(f.stage == "verify" for f in failures)
    import json as jsonlib

    extras = [jsonlib.loads(f.extra_json or "{}") for f in facts]
    assert any(e.get("listing_venue") for e in extras)
    employees = [f for f in facts if f.predicate == "employees"]
    assert any(f.value_num and f.value_num >= 10000 for f in employees)


def test_ingest_skip_when_ready(client, tiny_pdf, db_session):
    with tiny_pdf.open("rb") as f:
        up = client.post("/api/v1/documents", files={"file": ("tiny.pdf", f, "application/pdf")})
    doc_id = up.json()["id"]
    doc = db_session.get(Document, doc_id)
    doc.status = "ready"
    db_session.commit()
    r = client.post(f"/api/v1/documents/{doc_id}/ingest")
    assert r.status_code == 200
    assert r.json()["skipped"] is True


def test_ingest_running_conflict(client, tiny_pdf, db_session):
    from app.db.orm import Job

    with tiny_pdf.open("rb") as f:
        up = client.post("/api/v1/documents", files={"file": ("tiny.pdf", f, "application/pdf")})
    doc_id = up.json()["id"]
    db_session.add(Job(document_id=doc_id, stage="ingest", status="queued", attempts=0))
    db_session.commit()
    r = client.post(f"/api/v1/documents/{doc_id}/ingest")
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "INGEST_RUNNING"
