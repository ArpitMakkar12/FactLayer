from __future__ import annotations

from pathlib import Path

import fitz


def write_pdf(path: Path, paragraphs: list[str]) -> None:
    doc = fitz.open()
    page = doc.new_page()
    y = 72
    for para in paragraphs:
        page.insert_text((72, y), para, fontsize=11)
        y += 22
        if y > 740:
            page = doc.new_page()
            y = 72
    path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(path)
    doc.close()


def demo_pdfs(dest: Path) -> tuple[Path, Path]:
    a = dest / "demo-disclosure-a.pdf"
    b = dest / "demo-disclosure-b.pdf"
    write_pdf(
        a,
        [
            "Issuer disclosure pack.",
            "Consolidated revenue was 8,141 crore in FY 2023-24.",
            "The company is listed on NSE as of FY 2023-24 with 12,400 employees.",
            "Shipments were 2.8 billion in FY 2023-24 on a consolidated basis.",
            "Rated AA+ by CARE on the consolidated book.",
        ],
    )
    write_pdf(
        b,
        [
            "Earnings update note.",
            "Revenue stood at 8141 crore for FY 2023-24 on a consolidated basis.",
            "Revenue was 7,230 crore in FY 2022-23 on a consolidated basis.",
            "Headcount was 11,000 employees in FY 2023-24.",
            "Shipments reached 2.8 billion in FY 2023-24.",
        ],
    )
    return a, b
