from __future__ import annotations

import hashlib
import json
from pathlib import Path

import fitz

from app.db.orm import Document, Page, PdfTable


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_pdf(path: Path) -> tuple[list[dict], int]:
    """Return page dicts {page_no, text, tables} and page_count."""
    doc = fitz.open(path)
    pages: list[dict] = []
    try:
        for i, page in enumerate(doc, start=1):
            text = page.get_text("text") or ""
            tables: list[list[list[str]]] = []
            try:
                tf = page.find_tables()
                for t in tf.tables[:8]:
                    raw = t.extract()
                    tables.append([[c or "" for c in row] for row in raw[:40]])
            except Exception:
                pass
            pages.append({"page_no": i, "text": text, "tables": tables})
    finally:
        doc.close()
    return pages, len(pages)


def persist_pages(db, document: Document, pages: list[dict]) -> None:
    for p in pages:
        page = Page(document_id=document.id, page_no=p["page_no"], text=p["text"])
        db.add(page)
        db.flush()
        for idx, table in enumerate(p.get("tables") or []):
            db.add(
                PdfTable(
                    page_id=page.id,
                    ordinal=idx,
                    payload_json=json.dumps(table, ensure_ascii=False),
                )
            )
    document.page_count = len(pages)
    document.status = "parsed"
