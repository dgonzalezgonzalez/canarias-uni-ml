from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..models import JobRecord


class SpiderError(RuntimeError):
    """Raised when a source cannot be scraped with the current runtime setup."""


@dataclass(slots=True)
class SpiderResult:
    source: str
    records: list[JobRecord]


class Spider(Protocol):
    source: str

    def fetch(self, limit: int) -> SpiderResult:
        ...
