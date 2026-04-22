from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class DegreeCatalogRecord:
    source: str
    source_id: str
    university: str
    title: str
    branch: str | None
    modality: str | None
    credits: str | None
    status: str | None
    memory_url: str | None
    source_url: str | None
    description: str | None
    scraped_at: str

    @classmethod
    def now(cls) -> str:
        return datetime.now(timezone.utc).isoformat()

    def to_row(self) -> dict[str, Any]:
        return asdict(self)
