from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.orm import Embedding, Fact, Relation
from app.link.embed import jaccard
from app.settings import settings


def _tokens(emb: Embedding | None) -> list[str]:
    if not emb:
        return []
    try:
        return json.loads(emb.tokens_json)
    except Exception:
        return []


def candidate_pairs(db: Session, new_fact_ids: set[str]) -> list[tuple[Fact, Fact, float]]:
    """Pairs where at least one fact is new. Incremental: do not rebuild old-old pairs."""
    facts = list(db.scalars(select(Fact)).all())
    by_id = {f.id: f for f in facts}
    embs = {e.fact_id: e for e in db.scalars(select(Embedding)).all()}
    existing_pairs = {
        tuple(sorted((r.fact_a_id, r.fact_b_id)))
        for r in db.scalars(select(Relation)).all()
    }
    out: list[tuple[Fact, Fact, float]] = []
    new_facts = [by_id[i] for i in new_fact_ids if i in by_id]
    others = facts
    for nf in new_facts:
        scored: list[tuple[Fact, float]] = []
        nt = _tokens(embs.get(nf.id))
        for other in others:
            if other.id == nf.id:
                continue
            key = tuple(sorted((nf.id, other.id)))
            if key in existing_pairs:
                continue
            if nf.quote and other.quote and nf.quote == other.quote:
                continue
            if nf.page_id == other.page_id and nf.value_num is not None and nf.value_num == other.value_num:
                continue
            score = jaccard(nt, _tokens(embs.get(other.id)))
            same_pred = (nf.predicate or "").lower() == (other.predicate or "").lower() and nf.predicate
            if same_pred:
                score = max(score, 0.45)
            if score < settings.block_threshold and not same_pred:
                continue
            scored.append((other, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        for other, score in scored[:8]:
            a, b = (nf, other) if nf.id < other.id else (other, nf)
            out.append((a, b, score))
    # unique pairs
    uniq: dict[tuple[str, str], tuple[Fact, Fact, float]] = {}
    for a, b, s in out:
        uniq[(a.id, b.id)] = (a, b, s)
    return list(uniq.values())
