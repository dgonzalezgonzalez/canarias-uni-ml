from __future__ import annotations

import json

from ..io import write_csv_rows, write_sqlite_rows
from .memory_resolver import resolve_missing_memory
from .models import DegreeCatalogRecord
from .sources.aneca import fetch_aneca_degree_catalog, parse_aneca_records
from .sources.ruct import parse_ruct_records
from .university_registry import match_canary_university


def load_degree_catalog_from_fixture(fixture_path: str) -> list[dict]:
    with open(fixture_path, encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload


def build_degree_catalog(payload: dict) -> list[DegreeCatalogRecord]:
    records: list[DegreeCatalogRecord] = []
    records.extend(parse_aneca_records(payload.get("aneca", [])).records)
    records.extend(parse_ruct_records(payload.get("ruct", [])).records)
    _attach_university_registry(records)
    deduped: dict[tuple[str, str, str], object] = {}
    for record in records:
        key = (record.university.lower(), record.title.lower(), (record.title_type or "").lower())
        deduped[key] = record
    return sorted(deduped.values(), key=lambda item: (item.university, item.title))


def _attach_university_registry(records: list[DegreeCatalogRecord]) -> None:
    for record in records:
        match = match_canary_university(record.university)
        if not match:
            continue
        record.university = match.canonical_name
        record.university_id = match.university_id
        record.university_type = match.university_type


def write_degree_catalog(
    output_path: str,
    fixture_path: str | None = None,
    *,
    live_aneca: bool = False,
    cycles: tuple[str, ...] | None = None,
    limit: int | None = None,
    max_pages: int | None = None,
    with_report_text: bool = False,
    canary_only: bool = False,
    resolve_university_memory: bool = False,
    db_path: str | None = None,
) -> int:
    if fixture_path:
        payload = load_degree_catalog_from_fixture(fixture_path)
        records = build_degree_catalog(payload)
        if resolve_university_memory:
            for record in records:
                resolved = resolve_missing_memory(record)
                record.memory_url = resolved.memory_url or record.memory_url
                record.memory_resolution_source = resolved.source
                record.memory_resolution_status = resolved.status
                record.memory_resolution_error = resolved.error
    elif live_aneca:
        records = fetch_aneca_degree_catalog(
            cycles=cycles or ("grado", "master", "doctorado"),
            limit=limit,
            max_pages=max_pages,
            with_report_text=with_report_text,
            canary_only=canary_only,
            resolve_university_memory=resolve_university_memory,
        ).records
    else:
        print("[skip] Degree catalog requires --fixture or --live-aneca")
        return 1
    rows = [record.to_row() for record in records]
    written = write_csv_rows(rows, output_path)
    if db_path:
        write_sqlite_rows(rows, db_path, "degrees_catalog")
        print(f"[done] wrote {written} degree catalog rows to {output_path} and {db_path}")
    else:
        print(f"[done] wrote {written} degree catalog rows to {output_path}")
    return 0
