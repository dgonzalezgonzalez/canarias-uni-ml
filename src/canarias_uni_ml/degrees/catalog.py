from __future__ import annotations

import json

from ..io import write_csv_rows
from .sources.aneca import parse_aneca_records
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


def write_degree_catalog(output_path: str, fixture_path: str | None = None) -> int:
    if not fixture_path:
        print("[skip] Degree catalog currently requires --fixture for deterministic runs")
        return 1
    payload = load_degree_catalog_from_fixture(fixture_path)
    records = build_degree_catalog(payload)
    written = write_csv_rows([record.to_row() for record in records], output_path)
    print(f"[done] wrote {written} degree catalog rows to {output_path}")
    return 0
