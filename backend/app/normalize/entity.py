from __future__ import annotations

import re

_ws = re.compile(r"[^a-z0-9]+")


def entity_key(subject: str | None) -> str:
    """Lightweight alias key from a subject string. Not a company list."""
    s = _ws.sub(" ", (subject or "").lower()).strip()
    return " ".join(s.split()[:8])[:80]
