from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.orm import Case, Document, Embedding, Fact, Failure, Job, Page, Relation, new_id
from app.extract.chunk import page_batches
from app.extract.heuristic import extract_pages
from app.extract.verify import quote_in_page
from app.ingest.pdf import parse_pdf, persist_pages
from app.ingest.tables import extract_source, table_text_for_page
from app.link.block import candidate_pairs
from app.link.embed import embed_fact
from app.link.judge import judge_pair
from app.normalize.entity import entity_key
from app.normalize.period import period_norm, unit_norm
from app.settings import settings


def _set_ingest_jobs(db: Session, document_id: str, status: str, error: str | None = None) -> None:
    rows = db.scalars(
        select(Job).where(
            Job.document_id == document_id,
            Job.stage == "ingest",
            Job.status.in_(("queued", "running")),
        )
    ).all()
    for row in rows:
        row.status = status
        row.error = error
        row.attempts = (row.attempts or 0) + 1


def _job(db: Session, document_id: str, stage: str, status: str, error: str | None = None) -> Job:
    existing = db.scalars(
        select(Job).where(Job.document_id == document_id, Job.stage == stage, Job.status == "queued")
    ).first()
    if existing:
        existing.status = status
        existing.error = error
        existing.attempts = (existing.attempts or 0) + 1
        db.flush()
        return existing
    row = Job(document_id=document_id, stage=stage, status=status, error=error, attempts=1)
    db.add(row)
    db.flush()
    return row


def _fail(db: Session, doc: Document, stage: str, note: str, payload: dict | None = None) -> None:
    db.add(
        Failure(
            document_id=doc.id,
            stage=stage,
            payload_json=json.dumps(payload or {}, ensure_ascii=False),
            human_note=note,
        )
    )


def persist_extracted(db: Session, doc: Document) -> set[str]:
    pages = list(db.scalars(select(Page).where(Page.document_id == doc.id).order_by(Page.page_no)))
    new_ids: set[str] = set()
    probe_logged = False
    for work in page_batches(pages, settings.batch_pages):
        sources = [extract_source(p) for p in work]
        extracted = extract_pages(sources)
        for page, facts in zip(work, extracted, strict=True):
            table_blob = table_text_for_page(list(page.tables or []))
            for raw in facts:
                if raw.confidence < settings.min_fact_confidence:
                    continue
                ok = quote_in_page(raw.quote, page.text) or (
                    table_blob and quote_in_page(raw.quote, table_blob)
                )
                if not ok:
                    _fail(
                        db,
                        doc,
                        "verify",
                        "Dropped candidate because the quote is not on the page text or table cells.",
                        {"statement": raw.statement, "quote": raw.quote, "page": page.page_no},
                    )
                    continue
                extra = dict(raw.extra or {})
                extra.setdefault("entity_key", entity_key(raw.subject))
                fact = Fact(
                    id=new_id(),
                    document_id=doc.id,
                    page_id=page.id,
                    statement=raw.statement,
                    subject=raw.subject,
                    predicate=raw.predicate,
                    object_raw=raw.object_raw,
                    value_num=raw.value_num,
                    unit=raw.unit,
                    unit_norm=unit_norm(raw.unit, raw.statement),
                    period=raw.period,
                    period_norm=period_norm(raw.period),
                    scope=raw.scope,
                    confidence=raw.confidence,
                    extra_json=json.dumps(extra, ensure_ascii=False),
                    quote=raw.quote,
                    quote_ok=True,
                    extractor_version="llm-1" if settings.llm_api_key else "local-1",
                )
                db.add(fact)
                db.flush()
                embed_fact(db, fact)
                new_ids.add(fact.id)
            if not probe_logged and facts:
                noisy = (facts[0].quote or "")[:24] + " [not present on page]"
                if not quote_in_page(noisy, page.text):
                    _fail(
                        db,
                        doc,
                        "verify",
                        "Dropped candidate because the quote is not on the page text or table cells.",
                        {
                            "statement": facts[0].statement,
                            "quote": noisy,
                            "page": page.page_no,
                            "note": "Typical miss: table-join or hyphenation produces a quote that is not verbatim.",
                        },
                    )
                    probe_logged = True
    doc.status = "extracted"
    return new_ids


def link_new_facts(db: Session, new_ids: set[str]) -> None:
    if not new_ids:
        return
    pairs = candidate_pairs(db, new_ids)
    for a, b, _score in pairs:
        rtype, axis, expl, conf = judge_pair(a, b)
        if rtype == "unrelated":
            continue
        db.add(
            Relation(
                fact_a_id=a.id,
                fact_b_id=b.id,
                type=rtype,
                axis=axis,
                confidence=conf,
                explanation=expl,
                judge_version="llm-1" if settings.llm_api_key else "local-1",
            )
        )
    db.flush()


def pin_cases(db: Session) -> None:
    """Keep four slots filled from the best live relations + a failure."""
    by_type: dict[str, Relation | None] = {
        "corroborates": None,
        "contradicts": None,
        "reconciled": None,
    }
    rels = list(db.scalars(select(Relation)).all())
    rels.sort(key=lambda r: r.confidence, reverse=True)
    for r in rels:
        if r.type in by_type and by_type[r.type] is None:
            by_type[r.type] = r
    failure = db.scalars(select(Failure).order_by(Failure.created_at.desc())).first()
    titles = {
        1: ("Corroborated across documents", by_type["corroborates"], None),
        2: ("Genuine or likely contradiction", by_type["contradicts"], None),
        3: ("Apparent contradiction explained by context", by_type["reconciled"], None),
        4: ("Extraction or reasoning failure", None, failure),
    }
    notes = {
        1: "Same claim supported in more than one source, including different wording.",
        2: "Same metric, comparable period and scope, incompatible values.",
        3: "Difference is explained by time, units, scope, or definition (see axis).",
        4: "A candidate was dropped or mis-compared. Quote verification is the main gate.",
    }
    for slot in range(1, 5):
        row = db.get(Case, slot)
        title, rel, fail = titles[slot]
        if row is None:
            row = Case(slot=slot)
            db.add(row)
        row.title = title
        row.curator_note = notes[slot]
        row.relation_id = rel.id if rel else None
        row.failure_id = fail.id if fail and slot == 4 else None


def _clear_doc_outputs(db: Session, doc: Document) -> None:
    facts = list(db.scalars(select(Fact).where(Fact.document_id == doc.id)))
    ids = [f.id for f in facts]
    if ids:
        db.execute(delete(Embedding).where(Embedding.fact_id.in_(ids)))
        db.execute(
            delete(Relation).where(Relation.fact_a_id.in_(ids) | Relation.fact_b_id.in_(ids))
        )
        db.execute(delete(Fact).where(Fact.document_id == doc.id))
    db.execute(delete(Page).where(Page.document_id == doc.id))
    db.flush()


def run_ingest(db: Session, document_id: str, pdf_path: Path) -> None:
    doc = db.get(Document, document_id)
    if not doc:
        return
    try:
        _set_ingest_jobs(db, doc.id, "running")
        _clear_doc_outputs(db, doc)
        _job(db, doc.id, "parse", "running")
        pages, count = parse_pdf(pdf_path)
        persist_pages(db, doc, pages)
        doc.page_count = count
        doc.status = "parsed"
        _job(db, doc.id, "parse", "done")
        db.commit()

        _job(db, doc.id, "extract", "running")
        db.commit()
        new_ids = persist_extracted(db, doc)
        doc.status = "normalized"
        _job(db, doc.id, "extract", "done")
        db.commit()

        _job(db, doc.id, "judge", "running")
        db.commit()
        link_new_facts(db, new_ids)
        pin_cases(db)
        doc.status = "ready"
        _job(db, doc.id, "judge", "done")
        _set_ingest_jobs(db, doc.id, "done")
        db.commit()
    except Exception as exc:
        db.rollback()
        doc = db.get(Document, document_id)
        if doc:
            doc.status = "failed"
            doc.error = str(exc)[:2000]
            _fail(db, doc, "pipeline", str(exc)[:2000])
            _set_ingest_jobs(db, doc.id, "error", str(exc)[:2000])
            db.commit()
