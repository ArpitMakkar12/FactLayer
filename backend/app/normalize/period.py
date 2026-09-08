from __future__ import annotations

import re

FY = re.compile(r"FY\s*(20)?(\d{2})\s*[-–]?\s*(\d{2})?", re.I)
QFY = re.compile(r"Q([1-4])\s*FY\s*(20)?(\d{2})", re.I)
YEAR = re.compile(r"(?:CY|calendar year)\s*(20\d{2})", re.I)
YEAR2 = re.compile(r"\b(20\d{2})\b")


def period_norm(raw: str | None) -> str | None:
    if not raw:
        return None
    s = raw.strip()
    m = QFY.search(s)
    if m:
        yy = m.group(3)
        year = int(yy) + 2000 if len(yy) == 2 else int(yy)
        return f"Q{m.group(1)}-FY{year}"
    m = FY.search(s)
    if m:
        yy = m.group(2)
        year = int(yy) + 2000 if len(yy) == 2 else int(yy)
        # Indian FY label uses ending year when range present
        if m.group(3):
            end = int(m.group(3))
            if end < 100:
                end += 2000
            year = end if end > 2000 else year
        return f"FY{year}"
    m = YEAR.search(s)
    if m:
        return f"CY{m.group(1)}"
    m = YEAR2.search(s)
    if m:
        return f"CY{m.group(1)}"
    return s[:64]


def unit_norm(unit: str | None, sentence: str = "") -> str | None:
    blob = f"{unit or ''} {sentence}".lower()
    if any(x in blob for x in ("₹", "inr", "rs", "rupee", "crore", "lakh")):
        if "crore" in blob or " cr" in blob:
            return "INR_crore"
        if "lakh" in blob:
            return "INR_lakh"
        return "INR"
    if "percent" in blob or "%" in blob:
        return "percent"
    if "million" in blob:
        return "million"
    if "billion" in blob:
        return "billion"
    if unit:
        return unit.strip().lower()[:32]
    return None
