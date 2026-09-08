from enum import Enum


class DocumentStatus(str, Enum):
    uploaded = "uploaded"
    parsed = "parsed"
    extracted = "extracted"
    normalized = "normalized"
    ready = "ready"
    failed = "failed"


class RelationType(str, Enum):
    corroborates = "corroborates"
    contradicts = "contradicts"
    reconciled = "reconciled"
    unrelated = "unrelated"


class RelationAxis(str, Enum):
    time = "time"
    units = "units"
    scope = "scope"
    entity = "entity"
    definition = "definition"
