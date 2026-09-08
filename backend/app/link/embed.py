from __future__ import annotations

import json
import re

from app.db.orm import Embedding, Fact

TOKEN = re.compile(r"[a-z0-9]+")
STOP = {
    "the",
    "a",
    "an",
    "and",
    "of",
    "in",
    "to",
    "for",
    "on",
    "by",
    "with",
    "as",
    "at",
    "from",
    "is",
    "was",
    "were",
    "be",
}


def tokenize(*parts: str | None) -> list[str]:
    blob = " ".join(p or "" for p in parts).lower()
    toks = [t for t in TOKEN.findall(blob) if t not in STOP and len(t) > 1]
    # keep order unique
    seen: list[str] = []
    for t in toks:
        if t not in seen:
            seen.append(t)
    return seen[:48]


def jaccard(a: list[str], b: list[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def embed_fact(db, fact: Fact) -> None:
    tokens = tokenize(fact.subject, fact.predicate, fact.period_norm, fact.unit_norm)
    db.add(
        Embedding(
            fact_id=fact.id,
            model="token-jaccard",
            tokens_json=json.dumps(tokens),
        )
    )
