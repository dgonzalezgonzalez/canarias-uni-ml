from __future__ import annotations

import json

from ..io import write_csv_rows, write_sqlite_rows
from .sources.aneca import fetch_aneca_degree_catalog, parse_aneca_records
from .sources.ruct import parse_ruct_records


def load_degree_catalog_from_fixture(fixture_path: str) -> list[dict]:
    with open(fixture_path, encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload


def build_degree_catalog(payload: dict) -> list[object]:
    records = []
    records.extend(parse_aneca_records(payload.get("aneca", [])).records)
    records.extend(parse_ruct_records(payload.get("ruct", [])).records)
    deduped: dict[tuple[str, str], object] = {}
    for record in records:
        key = (record.university.lower(), record.title.lower())
        deduped[key] = record
    return sorted(deduped.values(), key=lambda item: (item.university, item.title))


def write_degree_catalog(
    output_path: str,
    fixture_path: str | None = None,
    *,
    live_aneca: bool = False,
    limit: int | None = None,
    max_pages: int | None = None,
    with_report_text: bool = False,
    canary_only: bool = False,
    db_path: str | None = None,
) -> int:
    if fixture_path:
        payload = load_degree_catalog_from_fixture(fixture_path)
        records = build_degree_catalog(payload)
    elif live_aneca:
        records = fetch_aneca_degree_catalog(
            limit=limit,
            max_pages=max_pages,
            with_report_text=with_report_text,
            canary_only=canary_only,
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
