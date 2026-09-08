from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return str(uuid4())


class Base(DeclarativeBase):
    pass


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    filename: Mapped[str] = mapped_column(Text)
    sha256: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default="uploaded")
    collection: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    page_count: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    pages: Mapped[list["Page"]] = relationship(back_populates="document", cascade="all, delete-orphan", passive_deletes=True)
    facts: Mapped[list["Fact"]] = relationship(back_populates="document", cascade="all, delete-orphan", passive_deletes=True)


class Page(Base):
    __tablename__ = "pages"
    __table_args__ = (UniqueConstraint("document_id", "page_no"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    page_no: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text, default="")

    document: Mapped[Document] = relationship(back_populates="pages")
    tables: Mapped[list["PdfTable"]] = relationship(back_populates="page", cascade="all, delete-orphan", passive_deletes=True)


class PdfTable(Base):
    __tablename__ = "tables"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    page_id: Mapped[str] = mapped_column(ForeignKey("pages.id", ondelete="CASCADE"))
    ordinal: Mapped[int] = mapped_column(Integer, default=0)
    payload_json: Mapped[str] = mapped_column(Text, default="[]")

    page: Mapped[Page] = relationship(back_populates="tables")


class Fact(Base):
    __tablename__ = "facts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    page_id: Mapped[str] = mapped_column(ForeignKey("pages.id", ondelete="CASCADE"))
    statement: Mapped[str] = mapped_column(Text)
    subject: Mapped[str] = mapped_column(Text, default="", index=True)
    predicate: Mapped[str] = mapped_column(Text, default="", index=True)
    object_raw: Mapped[str] = mapped_column(Text, default="")
    value_num: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(64), nullable=True)
    unit_norm: Mapped[str | None] = mapped_column(String(64), nullable=True)
    period: Mapped[str | None] = mapped_column(String(128), nullable=True)
    period_norm: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    scope: Mapped[str | None] = mapped_column(String(128), nullable=True)
    as_of: Mapped[str | None] = mapped_column(String(64), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    extra_json: Mapped[str] = mapped_column(Text, default="{}")
    quote: Mapped[str] = mapped_column(Text)
    quote_ok: Mapped[bool] = mapped_column(Boolean, default=False)
    extractor_version: Mapped[str] = mapped_column(String(32), default="local-1")

    document: Mapped[Document] = relationship(back_populates="facts")
    embedding: Mapped["Embedding | None"] = relationship(back_populates="fact", uselist=False, cascade="all, delete-orphan", passive_deletes=True)


class Embedding(Base):
    __tablename__ = "embeddings"

    fact_id: Mapped[str] = mapped_column(ForeignKey("facts.id", ondelete="CASCADE"), primary_key=True)
    model: Mapped[str] = mapped_column(String(64), default="token-jaccard")
    tokens_json: Mapped[str] = mapped_column(Text, default="[]")

    fact: Mapped[Fact] = relationship(back_populates="embedding")


class Relation(Base):
    __tablename__ = "relations"
    __table_args__ = (UniqueConstraint("fact_a_id", "fact_b_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    fact_a_id: Mapped[str] = mapped_column(ForeignKey("facts.id", ondelete="CASCADE"), index=True)
    fact_b_id: Mapped[str] = mapped_column(ForeignKey("facts.id", ondelete="CASCADE"), index=True)
    type: Mapped[str] = mapped_column(String(32), index=True)
    axis: Mapped[str | None] = mapped_column(String(32), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    explanation: Mapped[str] = mapped_column(Text, default="")
    judge_version: Mapped[str] = mapped_column(String(32), default="local-1")


class Case(Base):
    __tablename__ = "cases"

    slot: Mapped[int] = mapped_column(Integer, primary_key=True)
    relation_id: Mapped[str | None] = mapped_column(ForeignKey("relations.id", ondelete="SET NULL"), nullable=True)
    failure_id: Mapped[str | None] = mapped_column(ForeignKey("failures.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(Text, default="")
    curator_note: Mapped[str] = mapped_column(Text, default="")


class Failure(Base):
    __tablename__ = "failures"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    document_id: Mapped[str | None] = mapped_column(
        ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, index=True
    )
    stage: Mapped[str] = mapped_column(String(32), index=True)
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    human_note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    stage: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), default="queued")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
