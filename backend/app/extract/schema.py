from pydantic import BaseModel, Field


class ExtractedFact(BaseModel):
    statement: str
    subject: str
    predicate: str
    object_raw: str
    value_num: float | None = None
    unit: str | None = None
    period: str | None = None
    scope: str | None = None
    quote: str
    confidence: float = Field(ge=0, le=1)
    extra: dict = Field(default_factory=dict)
