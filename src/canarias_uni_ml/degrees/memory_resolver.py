from __future__ import annotations

from .models import DegreeCatalogRecord
from .sources.universities import (
    MemoryResolution,
    UAMMemoryResolver,
    UECMemoryResolver,
    UFPCMemoryResolver,
    ULLMemoryResolver,
    ULPGCMemoryResolver,
)


def resolve_missing_memory(record: DegreeCatalogRecord) -> MemoryResolution:
    if record.memory_url:
        return MemoryResolution(
            memory_url=record.memory_url,
            source=record.memory_resolution_source or "aneca",
            status=record.memory_resolution_status or "already_present",
            error=None,
        )
    resolver = _resolver_for_university(record.university_id)
    if not resolver:
        return MemoryResolution(
            memory_url=None,
            source="university_registry",
            status="unresolved",
            error="no_resolver_for_university",
        )
    return resolver.resolve(record.title)


def _resolver_for_university(university_id: str | None):
    if university_id == "ull":
        return ULLMemoryResolver()
    if university_id == "ulpgc":
        return ULPGCMemoryResolver()
    if university_id == "uec":
        return UECMemoryResolver()
    if university_id == "uam":
        return UAMMemoryResolver()
    if university_id == "ufpc":
        return UFPCMemoryResolver()
    return None
