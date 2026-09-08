from types import SimpleNamespace

from app.link.judge import local_judge, judge_pair
from app.normalize.period import period_norm, unit_norm


def _fact(**kwargs):
    base = dict(
        id="a",
        predicate="revenue",
        period="FY 2023-24",
        period_norm="FY2024",
        unit="crore",
        unit_norm="INR_crore",
        scope="consolidated",
        value_num=8141.0,
        object_raw="8141 crore",
        statement="revenue",
        quote="q",
    )
    base.update(kwargs)
    return SimpleNamespace(**base)


def test_period_norm_fy_range():
    assert period_norm("FY 2023-24") == "FY2024"
    assert period_norm("FY24") == "FY2024"
    assert period_norm("Q3 FY 2024") == "Q3-FY2024"


def test_unit_norm_crore():
    assert unit_norm("crore", "₹ 8,141 crore") == "INR_crore"
    assert unit_norm("%", "growth 12%") == "percent"


def test_contradict_gate_different_periods():
    a = _fact(id="a", period_norm="FY2024", value_num=8141)
    b = _fact(id="b", period_norm="FY2023", value_num=7230, object_raw="7230 crore")
    t, axis, expl, _ = local_judge(a, b)
    assert t == "reconciled"
    assert axis == "time"
    t2, axis2, _, _ = judge_pair(a, b)
    assert t2 != "contradicts"
    assert t2 == "reconciled"
    assert axis2 == "time"


def test_same_period_conflict_is_contradict():
    a = _fact(id="a", value_num=8141)
    b = _fact(id="b", value_num=11000, object_raw="11000 crore")
    t, axis, _, _ = local_judge(a, b)
    assert t == "contradicts"
    assert axis is None


def test_compatible_values_corroborate():
    a = _fact(id="a", value_num=8141)
    b = _fact(id="b", value_num=8141.2, object_raw="8141.2 crore")
    t, _, _, _ = local_judge(a, b)
    assert t == "corroborates"
