from __future__ import annotations

import json

from app.db.orm import Page, PdfTable


def table_text_for_page(tables: list[PdfTable]) -> str:
    parts: list[str] = []
    for t in tables:
        try:
            rows = json.loads(t.payload_json or "[]")
        except json.JSONDecodeError:
            continue
        for row in rows:
            cells = [str(c).strip() for c in row if str(c).strip()]
            if cells:
                parts.append(" | ".join(cells))
    return "\n".join(parts)


def extract_source(page: Page) -> str:
    """Page text plus flattened tables for recall; verify still uses page.text."""
    blob = page.text or ""
    extra = table_text_for_page(list(page.tables or []))
    if extra:
        blob = f"{blob}\n{extra}"
    return blob
