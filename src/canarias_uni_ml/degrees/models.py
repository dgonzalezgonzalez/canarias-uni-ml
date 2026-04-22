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
    title_type: str | None = None
    university_id: str | None = None
    university_type: str | None = None
    branch: str | None = None
    center: str | None = None
    modality: str | None = None
    language: str | None = None
    credits: str | None = None
    status: str | None = None
    memory_url: str | None = None
    report_url: str | None = None
    source_url: str | None = None
    memory_resolution_source: str | None = None
    memory_resolution_status: str | None = None
    memory_resolution_error: str | None = None
    description: str | None = None
    description_source: str | None = None
    scraped_at: str = ""

    @classmethod
    def now(cls) -> str:
        return datetime.now(timezone.utc).isoformat()

    def to_row(self) -> dict[str, Any]:
        return asdict(self)
