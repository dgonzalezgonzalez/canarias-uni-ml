from __future__ import annotations

import csv
import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Iterable


def ensure_parent(path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def _rowify(item):
    if is_dataclass(item):
        return asdict(item)
    return item


def write_csv_rows(rows: Iterable[object], output_path: str | Path) -> int:
    data = [_rowify(row) for row in rows]
    ensure_parent(output_path)
    if not data:
        return 0
    with open(output_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(data[0].keys()))
        writer.writeheader()
        writer.writerows(data)
    return len(data)


def write_jsonl_rows(rows: Iterable[object], output_path: str | Path) -> int:
    count = 0
    ensure_parent(output_path)
    with open(output_path, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(_rowify(row), ensure_ascii=False) + "\n")
            count += 1
    return count
