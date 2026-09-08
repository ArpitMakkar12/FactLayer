from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.db.orm import Base
from app.db.session import get_db
from app.ingest.demo_pdf import demo_pdfs, write_pdf
from app.main import app


@asynccontextmanager
async def _noop_lifespan(app):
    yield


app.router.lifespan_context = _noop_lifespan


@pytest.fixture
def workdir():
    root = Path(__file__).resolve().parent / "_work"
    root.mkdir(exist_ok=True)
    path = root / uuid.uuid4().hex
    path.mkdir()
    yield path


@pytest.fixture
def db_session(workdir, monkeypatch):
    db_path = workdir / "test.db"
    engine = create_engine(
        f"sqlite:///{db_path.as_posix()}",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def _pragma(conn, _):
        cur = conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = Session()
    monkeypatch.setattr("app.db.session.SessionLocal", Session)
    monkeypatch.setattr("app.api.documents.SessionLocal", Session)
    monkeypatch.setattr("app.api.samples.SessionLocal", Session)
    monkeypatch.setattr("app.settings.settings.upload_dir", str(workdir / "uploads"))
    (workdir / "uploads").mkdir(exist_ok=True)

    def _get_db():
        s = Session()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = _get_db
    yield session
    session.close()
    app.dependency_overrides.clear()


@pytest.fixture
def client(db_session):
    return TestClient(app)


@pytest.fixture
def sample_pdfs(workdir):
    return demo_pdfs(workdir)


@pytest.fixture
def tiny_pdf(workdir):
    path = workdir / "tiny.pdf"
    write_pdf(path, ["Consolidated revenue was 100 crore in FY 2023-24."])
    return path
