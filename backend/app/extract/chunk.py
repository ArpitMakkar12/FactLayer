from __future__ import annotations

from collections.abc import Iterable, Sequence

from app.db.orm import Page


def skip_empty(pages: Sequence[Page], min_chars: int = 40) -> list[Page]:
    return [p for p in pages if len((p.text or "").strip()) >= min_chars]


def page_batches(
    pages: Sequence[Page], batch_size: int, min_chars: int = 40
) -> Iterable[list[Page]]:
    """Yield non-empty page batches (large-PDF brownie: skip short pages)."""
    for start in range(0, len(pages), max(1, batch_size)):
        work = skip_empty(pages[start : start + batch_size], min_chars)
        if work:
            yield work
