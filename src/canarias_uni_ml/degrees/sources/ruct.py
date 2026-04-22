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
            title_type=item.get("title_type") or item.get("tipo_titulo"),
            university_id=item.get("university_id"),
            university_type=item.get("university_type"),
            branch=item.get("branch") or item.get("rama"),
            center=item.get("center") or item.get("centro"),
            modality=item.get("modality") or item.get("modalidad"),
            language=item.get("language") or item.get("idioma"),
            credits=str(item.get("credits")) if item.get("credits") is not None else None,
            status=item.get("status") or item.get("estado"),
            memory_url=item.get("memory_url") or item.get("memoria"),
            report_url=item.get("report_url") or item.get("informe"),
            source_url=item.get("source_url") or item.get("url"),
            memory_resolution_source=item.get("memory_resolution_source"),
            memory_resolution_status=item.get("memory_resolution_status"),
            memory_resolution_error=item.get("memory_resolution_error"),
            description=item.get("description"),
            description_source=item.get("description_source"),
            scraped_at=DegreeCatalogRecord.now(),
        )
        for item in payload
    ]
    return DegreeSourceResult(source="ruct", records=records)
