from __future__ import annotations

from ..models import DegreeCatalogRecord
from .base import DegreeSourceResult


def parse_aneca_records(payload: list[dict]) -> DegreeSourceResult:
    records = [
        DegreeCatalogRecord(
            source="aneca",
            source_id=str(item.get("id") or item.get("codigo") or item.get("title")),
            university=item.get("university") or item.get("universidad") or "Unknown",
            title=item.get("title") or item.get("titulo") or "Unknown title",
            branch=item.get("branch") or item.get("rama"),
            modality=item.get("modality") or item.get("modalidad"),
            credits=str(item.get("credits")) if item.get("credits") is not None else None,
            status=item.get("status") or item.get("estado"),
            memory_url=item.get("memory_url") or item.get("memoria"),
            source_url=item.get("source_url") or item.get("url"),
            description=item.get("description"),
            scraped_at=DegreeCatalogRecord.now(),
        )
        for item in payload
    ]
    return DegreeSourceResult(source="aneca", records=records)
