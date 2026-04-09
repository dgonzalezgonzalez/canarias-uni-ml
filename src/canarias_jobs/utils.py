from __future__ import annotations

import csv
import os
import re
from pathlib import Path
from typing import Iterable

from dateutil import parser as date_parser

from .models import JobRecord


ISLAND_TO_PROVINCE = {
    "TENERIFE": "Santa Cruz de Tenerife",
    "LA PALMA": "Santa Cruz de Tenerife",
    "LA GOMERA": "Santa Cruz de Tenerife",
    "EL HIERRO": "Santa Cruz de Tenerife",
    "GRAN CANARIA": "Las Palmas",
    "LANZAROTE": "Las Palmas",
    "FUERTEVENTURA": "Las Palmas",
}


def clean_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


def parse_date(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return date_parser.parse(value, dayfirst=True, fuzzy=True).isoformat()
    except (ValueError, TypeError, OverflowError):
        return clean_text(value)


def infer_province_from_island(island: str | None) -> str | None:
    if not island:
        return None
    return ISLAND_TO_PROVINCE.get(clean_text(island or "").upper())


def ensure_parent(path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def write_csv(records: Iterable[JobRecord], output_path: str | Path) -> int:
    records = list(records)
    ensure_parent(output_path)
    if not records:
        return 0
    with open(output_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0].to_row().keys()))
        writer.writeheader()
        for record in records:
            writer.writerow(record.to_row())
    return len(records)


def env_flag(name: str, default: bool = True) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}
