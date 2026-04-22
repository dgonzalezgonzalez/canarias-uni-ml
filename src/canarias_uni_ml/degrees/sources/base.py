from __future__ import annotations

from dataclasses import dataclass

from ..models import DegreeCatalogRecord


@dataclass(slots=True)
class DegreeSourceResult:
    source: str
    records: list[DegreeCatalogRecord]
