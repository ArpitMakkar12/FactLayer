from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.api.cases import router as cases_router
from app.api.documents import router as documents_router
from app.api.errors import error
from app.api.facts import router as facts_router
from app.api.failures import router as failures_router
from app.api.relations import router as relations_router
from app.api.samples import router as samples_router
from app.db.session import init_db

WEB = Path(__file__).resolve().parent / "web"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="FactLayer",
    version="1.0.0",
    description="Grounded facts from PDFs with corroboration, contradiction, and context.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents_router, prefix="/api/v1")
app.include_router(facts_router, prefix="/api/v1")
app.include_router(relations_router, prefix="/api/v1")
app.include_router(cases_router, prefix="/api/v1")
app.include_router(failures_router, prefix="/api/v1")
app.include_router(samples_router, prefix="/api/v1")



@app.exception_handler(HTTPException)
async def http_exc(_request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content=error("VALIDATION", str(exc.detail)),
    )


@app.exception_handler(RequestValidationError)
async def valid_exc(_request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content=error("VALIDATION", "Request validation failed", {"errors": exc.errors()}),
    )


@app.get("/api/v1/stats")
def stats():
    from sqlalchemy import func, select
    from app.db.orm import Document, Fact, Failure, Relation
    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        docs = db.scalar(select(func.count()).select_from(Document)) or 0
        facts = db.scalar(select(func.count()).select_from(Fact).where(Fact.quote_ok.is_(True))) or 0
        rels = db.scalar(select(func.count()).select_from(Relation)) or 0
        fails = db.scalar(select(func.count()).select_from(Failure)) or 0
        # Per-type relation counts
        corr = db.scalar(select(func.count()).select_from(Relation).where(Relation.type == "corroborates")) or 0
        contr = db.scalar(select(func.count()).select_from(Relation).where(Relation.type == "contradicts")) or 0
        recon = db.scalar(select(func.count()).select_from(Relation).where(Relation.type == "reconciled")) or 0
        return {
            "documents": docs, "facts": facts, "relations": rels, "failures": fails,
            "relations_by_type": {"corroborates": corr, "contradicts": contr, "reconciled": recon},
        }
    finally:
        db.close()


@app.get("/health")
@app.get("/api/v1/health")
def health():
    return {"ok": True, "service": "factlayer"}


@app.get("/")
def index():
    return FileResponse(WEB / "index.html")


app.mount("/static", StaticFiles(directory=WEB), name="static")
