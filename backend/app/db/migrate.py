"""Schema is incremental: create_all plus extra_json on facts from day one."""

from app.db.session import init_db


def migrate() -> None:
    init_db()
