from __future__ import annotations

import re
import unicodedata


_ws = re.compile(r"\s+")


def collapse_ws(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    return _ws.sub(" ", text).strip()


def quote_in_page(quote: str, page_text: str) -> bool:
    q = collapse_ws(quote)
    t = collapse_ws(page_text)
    if not q or len(q) < 12:
        return False
    if q in t:
        return True
    # allow small quote windows from tables (newlines already collapsed)
    if len(q) >= 20:
        tokens = q.split()
        if len(tokens) >= 4:
            window = " ".join(tokens[:8])
            if window in t:
                return True
    return False
