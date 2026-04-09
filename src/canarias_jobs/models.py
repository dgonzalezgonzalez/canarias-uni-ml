from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class JobRecord:
    source: str
    external_id: str
    title: str
    company: str | None
    description: str | None
    salary_text: str | None
    salary_min: str | None
    salary_max: str | None
    salary_currency: str | None
    salary_period: str | None
    publication_date: str | None
    update_date: str | None
    province: str | None
    municipality: str | None
    island: str | None
    raw_location: str | None
    contract_type: str | None
    workday: str | None
    schedule: str | None
    vacancies: str | None
    source_url: str
    scraped_at: str

    @classmethod
    def now(cls) -> str:
        return datetime.now(timezone.utc).isoformat()

    def to_row(self) -> dict[str, Any]:
        return asdict(self)

