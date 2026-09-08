from __future__ import annotations

from app.db.orm import Fact
from app.domain.models import RelationAxis, RelationType
from app.link.prompts import JUDGE_PROMPT
from app.llm.client import complete_json


def _close(a: float, b: float, rel: float = 0.08, abs_tol: float = 0.5) -> bool:
    if a == 0 and b == 0:
        return True
    return abs(a - b) <= max(abs_tol, rel * max(abs(a), abs(b)))


def local_judge(a: Fact, b: Fact) -> tuple[str, str | None, str, float]:
    pred_a, pred_b = (a.predicate or "").lower(), (b.predicate or "").lower()
    same_metric = pred_a and (pred_a == pred_b or pred_a in pred_b or pred_b in pred_a)
    if not same_metric:
        return RelationType.unrelated.value, None, "Different metrics or predicates.", 0.4

    pa, pb = a.period_norm, b.period_norm
    ua, ub = a.unit_norm, b.unit_norm
    sa, sb = (a.scope or "").lower(), (b.scope or "").lower()
    same_period = (not pa or not pb) or pa == pb
    same_unit = (not ua or not ub) or ua == ub
    same_scope = (not sa or not sb) or sa == sb

    va, vb = a.value_num, b.value_num
    values_ok = va is not None and vb is not None
    values_close = values_ok and _close(va, vb)
    values_conflict = values_ok and not _close(va, vb, rel=0.10)

    if same_period and same_unit and same_scope and values_close:
        return (
            RelationType.corroborates.value,
            None,
            f"Same metric '{a.predicate}' with compatible values "
            f"({a.object_raw} vs {b.object_raw}) across documents, even if wording differs. "
            f"Quotes: “{(a.quote or '')[:120]}” and “{(b.quote or '')[:120]}”.",
            0.82,
        )

    if same_period and same_unit and same_scope and values_conflict:
        return (
            RelationType.contradicts.value,
            None,
            f"Same metric '{a.predicate}', overlapping period {pa or pb}, "
            f"and comparable scope/units, but values differ ({a.object_raw} vs {b.object_raw}). "
            f"Quotes: “{(a.quote or '')[:120]}” and “{(b.quote or '')[:120]}”.",
            0.78,
        )

    axis = None
    reason = []
    if not same_period and pa and pb:
        axis = RelationAxis.time.value
        reason.append(f"periods {pa} vs {pb}")
    elif not same_unit and ua and ub:
        axis = RelationAxis.units.value
        reason.append(f"units {ua} vs {ub}")
    elif not same_scope and sa and sb:
        axis = RelationAxis.scope.value
        reason.append(f"scope {sa} vs {sb}")
    elif values_ok and not values_close:
        axis = RelationAxis.definition.value
        reason.append("values differ and period/scope/units are not fully aligned")

    if axis:
        return (
            RelationType.reconciled.value,
            axis,
            "Apparent conflict on '{pred}' is explained by {why}.".format(
                pred=a.predicate, why="; ".join(reason)
            )
            + f" Evidence: {a.object_raw} vs {b.object_raw}.",
            0.8,
        )

    if values_close or not values_ok:
        return (
            RelationType.corroborates.value,
            None,
            f"Related statements of '{a.predicate}' support each other across sources.",
            0.6,
        )

    return RelationType.unrelated.value, None, "Insufficient overlap to compare.", 0.35


def _period_contradict_gate(
    a: Fact, b: Fact, result: tuple[str, str | None, str, float]
) -> tuple[str, str | None, str, float]:
    """G3: different normalized periods cannot be labeled contradicts."""
    t, axis, expl, conf = result
    pa, pb = a.period_norm, b.period_norm
    if t == "contradicts" and pa and pb and pa != pb:
        return (
            "reconciled",
            "time",
            f"{expl} Periods differ ({pa} vs {pb}), so this is reconciled on time, not a contradiction.",
            conf,
        )
    return result


def judge_pair(a: Fact, b: Fact) -> tuple[str, str | None, str, float]:
    local = local_judge(a, b)
    from app.settings import settings

    if not settings.llm_api_key:
        return _period_contradict_gate(a, b, local)
    payload = {
        "a": {
            "statement": a.statement,
            "value": a.object_raw,
            "period": a.period,
            "scope": a.scope,
            "unit": a.unit,
            "quote": a.quote,
        },
        "b": {
            "statement": b.statement,
            "value": b.object_raw,
            "period": b.period,
            "scope": b.scope,
            "unit": b.unit,
            "quote": b.quote,
        },
    }
    data = complete_json(
        JUDGE_PROMPT.format(a=payload["a"], b=payload["b"]),
        model=settings.judge_model,
    )
    if not data:
        return _period_contradict_gate(a, b, local)
    t = data.get("type") or local[0]
    if t not in {"unrelated", "corroborates", "contradicts", "reconciled"}:
        t = local[0]
    axis = data.get("axis")
    expl = data.get("explanation") or local[2]
    conf = float(data.get("confidence") or local[3])
    return _period_contradict_gate(a, b, (t, axis, expl, conf))
