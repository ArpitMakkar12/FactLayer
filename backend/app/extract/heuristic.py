from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.extract.extra import extra_from_text
from app.extract.prompts import EXTRACT_PROMPT
from app.extract.schema import ExtractedFact
from app.llm.client import complete_json
from app.settings import settings

NUMBER = re.compile(
    r"(?<![\w.])("
    r"\d{1,3}(?:,\d{2,3})+(?:\.\d+)?"
    r"|\d+\.\d+"
    r"|\d+"
    r")(?![\w])"
)

UNIT_WORDS = (
    "crore",
    "cr ",
    "lakh",
    "million",
    "billion",
    "percent",
    "%",
    "km",
    "mt",
    "gw",
    "mw",
    "tonne",
    "rupee",
    "inr",
    "rs.",
    "₹",
    "usd",
    "$",
    "employees",
    "pin codes",
    "pincodes",
    "shipments",
    "tonnes",
)

PERIOD_RE = re.compile(
    r"(FY\s*20\d{2}\s*[-–]\s*\d{2}"
    r"|FY\s*20\d{2}"
    r"|Q[1-4]\s*FY\s*20\d{2}"
    r"|calendar year 20\d{2}"
    r"|CY\s*20\d{2}"
    r"|20\d{2}-\d{2}"
    r"|fiscal 20\d{2})",
    re.I,
)

SCOPE_RE = re.compile(
    r"\b(consolidated|standalone|worldwide|domestic|global|national|export|import)\b",
    re.I,
)

SENTENCE = re.compile(r"(?<=[.!?])\s+|\n+")


def _parse_number(raw: str) -> float | None:
    try:
        return float(raw.replace(",", ""))
    except ValueError:
        return None


def _metric_matches(sentence: str):
    """Ignore years that belong to FY/CY labels so 12,400 is not extracted as 2023."""
    masked = PERIOD_RE.sub(" ", sentence)
    return list(NUMBER.finditer(masked))


def _unit_near(sentence: str) -> str | None:
    low = sentence.lower()
    for u in UNIT_WORDS:
        if u in low:
            return u.strip().replace(".", "")
    return None


def _subject(sentence: str) -> str:
    words = sentence.split()
    return " ".join(words[:8])[:120]


def _predicate(sentence: str, unit: str | None) -> str:
    low = sentence.lower()
    for key in (
        "revenue",
        "income",
        "profit",
        "loss",
        "ebitda",
        "gdp",
        "inflation",
        "cpi",
        "growth",
        "employees",
        "headcount",
        "shipments",
        "pin code",
        "facility",
        "gateways",
        "tonnage",
        "gmv",
        "volume",
    ):
        if key in low:
            return key
    return (unit or "value").strip()


def heuristic_extract(page_text: str, max_facts: int = 18) -> list[ExtractedFact]:
    facts: list[ExtractedFact] = []
    seen: set[str] = set()
    chunks = [c.strip() for c in SENTENCE.split(page_text) if len(c.strip()) > 24]
    for sent in chunks:
        if len(facts) >= max_facts:
            break
        period_m = PERIOD_RE.search(sent)
        period = period_m.group(0).strip() if period_m else None
        scope_m = SCOPE_RE.search(sent)
        scope = scope_m.group(1).lower() if scope_m else None
        unit = _unit_near(sent)
        matches = _metric_matches(sent)
        if not matches:
            continue
        # prefer sentences that look like metrics
        score = 0.45
        if unit:
            score += 0.2
        if period:
            score += 0.1
        if any(k in sent.lower() for k in ("revenue", "gdp", "profit", "crore", "percent", "growth")):
            score += 0.15
        if score < settings.min_fact_confidence:
            continue
        raw = matches[0].group(1)
        value = _parse_number(raw)
        quote = sent[:400]
        key = f"{raw}|{period}|{_predicate(sent, unit)}"
        if key in seen:
            continue
        seen.add(key)
        pred = _predicate(sent, unit)
        facts.append(
            ExtractedFact(
                statement=sent[:300],
                subject=_subject(sent),
                predicate=pred,
                object_raw=raw if value is None else (f"{raw} {unit}" if unit else raw),
                value_num=value,
                unit=unit,
                period=period,
                scope=scope,
                quote=quote,
                confidence=min(score, 0.95),
                extra=extra_from_text(sent),
            )
        )
    return facts


def llm_extract(page_text: str) -> list[ExtractedFact]:
    data = complete_json(EXTRACT_PROMPT + page_text[:12000])
    if not data:
        return []
    out: list[ExtractedFact] = []
    for item in data.get("facts") or []:
        try:
            out.append(ExtractedFact.model_validate(item))
        except Exception:
            continue
    return out


def extract_page(page_text: str) -> list[ExtractedFact]:
    local = heuristic_extract(page_text)
    if not settings.llm_api_key:
        return local
    llm = llm_extract(page_text)
    if not llm:
        return local
    # prefer LLM, keep local if disjoint predicates
    return llm[:24]


def extract_pages(texts: list[str]) -> list[list[ExtractedFact]]:
    if not texts:
        return []
    if not settings.llm_api_key:
        return [extract_page(t) for t in texts]
    results: list[list[ExtractedFact] | None] = [None] * len(texts)
    with ThreadPoolExecutor(max_workers=settings.llm_concurrency) as pool:
        futs = {pool.submit(extract_page, t): i for i, t in enumerate(texts)}
        for fut in as_completed(futs):
            results[futs[fut]] = fut.result()
    return [r or [] for r in results]
