from __future__ import annotations

from ..models import DegreeCatalogRecord
from .base import DegreeSourceResult


def parse_ruct_records(payload: list[dict]) -> DegreeSourceResult:
    records = [
        DegreeCatalogRecord(
            source="ruct",
            source_id=str(item.get("id") or item.get("codigo") or item.get("title")),
            university=item.get("university") or item.get("universidad") or "Unknown",
            title=item.get("title") or item.get("titulo") or "Unknown title",
            branch=item.get("branch") or item.get("rama"),
            center=item.get("center") or item.get("centro"),
            modality=item.get("modality") or item.get("modalidad"),
            language=item.get("language") or item.get("idioma"),
            credits=str(item.get("credits")) if item.get("credits") is not None else None,
            status=item.get("status") or item.get("estado"),
            memory_url=item.get("memory_url") or item.get("memoria"),
            report_url=item.get("report_url") or item.get("informe"),
            source_url=item.get("source_url") or item.get("url"),
            description=item.get("description"),
            description_source=item.get("description_source"),
            scraped_at=DegreeCatalogRecord.now(),
        )
        for item in payload
    ]
    return DegreeSourceResult(source="ruct", records=records)
