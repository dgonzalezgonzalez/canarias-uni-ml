from __future__ import annotations

import json

from ..io import write_csv_rows, write_sqlite_rows
from .completeness import ensure_min_inventory_completeness, validate_degree_catalog_quality
from .coverage import ensure_min_description_coverage
from .memory_resolver import resolve_missing_memory
from .models import DegreeCatalogRecord
from .sources.aneca import fetch_aneca_degree_catalog, parse_aneca_records
from .sources.ruct import parse_ruct_records
from .sources.university_official import fetch_university_official_catalog
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
    live_universities: bool = False,
    cycles: tuple[str, ...] | None = None,
    limit: int | None = None,
    max_pages: int | None = None,
    http_timeout: int = 30,
    skip_description_fetch: bool = False,
    with_report_text: bool = False,
    min_description_coverage: float | None = None,
    min_inventory_completeness: float | None = None,
    require_all_scoped_universities: bool = False,
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
    elif live_universities:
        records = fetch_university_official_catalog(
            cycles=cycles or ("grado", "master", "doctorado"),
            limit=limit,
            timeout=http_timeout,
            fetch_descriptions=not skip_description_fetch,
        ).records
    elif live_aneca:
        records = fetch_aneca_degree_catalog(
            cycles=cycles or ("grado", "master", "doctorado"),
            limit=limit,
            max_pages=max_pages,
            timeout=http_timeout,
            with_report_text=with_report_text,
            use_official_secondary_fallback=True,
            canary_only=canary_only,
            resolve_university_memory=resolve_university_memory,
        ).records
    else:
        print("[skip] Degree catalog requires --fixture, --live-universities, or --live-aneca")
        return 1
    _normalize_description_fields(records)
    rows = [record.to_row() for record in records]
    if live_universities:
        quality = validate_degree_catalog_quality(rows)
        if not quality.ok:
            print("[error] catalog quality gate failed")
            for message in quality.blocked_rows[:20]:
                print(f"[error] {message}")
            if len(quality.blocked_rows) > 20:
                print(f"[error] ... {len(quality.blocked_rows) - 20} more blocked rows")
            return 1
    inventory_ok, inventory_message = ensure_min_inventory_completeness(
        rows,
        min_inventory_completeness,
        require_all_scoped_universities=require_all_scoped_universities,
    )
    print(f"[info] {inventory_message}")
    if not inventory_ok:
        print("[error] inventory completeness requirement not met")
        return 1
    ok, coverage_message = ensure_min_description_coverage(rows, min_description_coverage)
    print(f"[info] {coverage_message}")
    if min_description_coverage is not None and not ok:
        print(f"[error] minimum description coverage not met: {min_description_coverage:.2%}")
        return 1
    written = write_csv_rows(rows, output_path)
    if db_path:
        write_sqlite_rows(rows, db_path, "degrees_catalog")
        print(f"[done] wrote {written} degree catalog rows to {output_path} and {db_path}")
    else:
        print(f"[done] wrote {written} degree catalog rows to {output_path}")
    return 0


def _normalize_description_fields(records: list[DegreeCatalogRecord]) -> None:
    for record in records:
        has_description = bool((record.description or "").strip())
        if has_description and not record.description_status:
            record.description_status = "ok"
        if not has_description and not record.description_status:
            record.description_status = "missing"
        if not record.description_source_type and record.description_source:
            record.description_source_type = record.description_source
        if not record.description_source_url:
            if record.description_source_type == "memory_pdf" and record.memory_url:
                record.description_source_url = (record.memory_url.split("|")[0] if record.memory_url else None)
            elif record.description_source_type == "official_secondary":
                record.description_source_url = record.source_url or record.report_url
