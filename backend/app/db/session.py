from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.db.orm import Base
from app.settings import ROOT, settings

_db_url = settings.database_url
if _db_url.startswith("sqlite:///./"):
    db_path = Path(__file__).resolve().parents[1] / "app.db"
    _db_url = f"sqlite:///{db_path.as_posix()}"

engine = create_engine(
    _db_url,
    connect_args={"check_same_thread": False, "timeout": 30.0} if _db_url.startswith("sqlite") else {},
)

if _db_url.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def _sqlite_pragma(dbapi_conn, _):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    # Lightweight migration: add new columns to existing tables
    with engine.connect() as conn:
        try:
            conn.execute(__import__("sqlalchemy").text(
                "ALTER TABLE documents ADD COLUMN collection VARCHAR(128)"
            ))
            conn.commit()
        except Exception:
            pass  # column already exists


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
