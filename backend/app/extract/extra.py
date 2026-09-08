from __future__ import annotations

import re

LISTED = re.compile(r"listed on\s+([A-Za-z]{2,12})", re.I)
RATING = re.compile(r"rated\s+([A-Za-z0-9+-]+)\s+by\s+([A-Za-z][\w.& -]{1,40})", re.I)
LABEL = re.compile(r"\b([A-Za-z][A-Za-z ]{1,24}):\s*([A-Za-z0-9./_%+-]+)")


def extra_from_text(sentence: str) -> dict:
    """Catch attributes that do not fit core columns (evolving schema)."""
    extra: dict = {}
    m = LISTED.search(sentence or "")
    if m:
        extra["listing_venue"] = m.group(1).upper()
    m = RATING.search(sentence or "")
    if m:
        extra["rating"] = m.group(1)
        extra["rating_agency"] = m.group(2).strip()
    for lm in LABEL.finditer(sentence or ""):
        key = lm.group(1).strip().lower().replace(" ", "_")
        if key in {"subject", "period", "scope", "unit", "value"}:
            continue
        extra.setdefault(key, lm.group(2))
    return extra
