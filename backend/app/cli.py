"""CLI: python -m app.cli ingest FILE.pdf | dump-samples | load-samples | demo"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.db.orm import Document
from app.db.session import SessionLocal, init_db
from app.ingest.demo_pdf import demo_pdfs
from app.ingest.pdf import sha256_bytes
from app.jobs.pipeline import run_ingest
from app.jobs.samples import dump_layer, load_layer
from app.settings import ROOT, settings


def _ingest_file(path: Path) -> str:
    init_db()
    raw = path.read_bytes()
    digest = sha256_bytes(raw)
    dest = Path(settings.upload_dir) / f"{digest}.pdf"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        dest.write_bytes(raw)
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.sha256 == digest).one_or_none()
        if doc and doc.status == "ready":
            print(f"reused {doc.id} (already ready)")
            return doc.id
        if not doc:
            doc = Document(filename=path.name, sha256=digest, status="uploaded")
            db.add(doc)
            db.commit()
            db.refresh(doc)
        run_ingest(db, doc.id, dest)
        print(f"{doc.id} {doc.status}")
        return doc.id
    finally:
        db.close()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="factlayer")
    sub = p.add_subparsers(dest="cmd", required=True)
    ing = sub.add_parser("ingest")
    ing.add_argument("pdf")
    sub.add_parser("dump-samples")
    sub.add_parser("load-samples")
    sub.add_parser("demo")
    corpus = sub.add_parser("ingest-dir")
    corpus.add_argument("folder")
    args = p.parse_args(argv)

    sample = ROOT / "data" / "samples" / "layer.json"
    if args.cmd == "ingest":
        _ingest_file(Path(args.pdf))
        return 0
    if args.cmd == "dump-samples":
        init_db()
        db = SessionLocal()
        try:
            sample.parent.mkdir(parents=True, exist_ok=True)
            dump_layer(db, sample)
            print(sample)
        finally:
            db.close()
        return 0
    if args.cmd == "load-samples":
        init_db()
        db = SessionLocal()
        try:
            print(load_layer(db, sample))
            db.commit()
        finally:
            db.close()
        return 0
    if args.cmd == "demo":
        a, b = demo_pdfs(ROOT / "data" / "samples")
        _ingest_file(a)
        _ingest_file(b)
        init_db()
        db = SessionLocal()
        try:
            from app.jobs.pipeline import pin_cases

            pin_cases(db)
            db.commit()
            sample.parent.mkdir(parents=True, exist_ok=True)
            dump_layer(db, sample)
            print("wrote", sample)
        finally:
            db.close()
        return 0
    if args.cmd == "ingest-dir":
        folder = Path(args.folder)
        pdfs = sorted(folder.glob("*.pdf"))
        if not pdfs:
            print("no PDFs in", folder)
            return 1
        for pdf in pdfs:
            print("ingest", pdf.name)
            _ingest_file(pdf)
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
