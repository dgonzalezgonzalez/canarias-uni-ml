from __future__ import annotations

import csv
import json
import sqlite3
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


def write_sqlite_rows(rows: Iterable[object], db_path: str | Path, table_name: str) -> int:
    data = [_rowify(row) for row in rows]
    ensure_parent(db_path)
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(f'DROP TABLE IF EXISTS "{table_name}"')
        if not data:
            conn.commit()
            return 0
        columns = list(data[0].keys())
        column_defs = ", ".join(f'"{column}" TEXT' for column in columns)
        cursor.execute(f'CREATE TABLE "{table_name}" ({column_defs})')
        placeholders = ", ".join("?" for _ in columns)
        quoted_columns = ", ".join(f'"{column}"' for column in columns)
        insert_sql = f'INSERT INTO "{table_name}" ({quoted_columns}) VALUES ({placeholders})'
        cursor.executemany(insert_sql, [[row.get(column) for column in columns] for row in data])
        conn.commit()
        return len(data)
    finally:
        conn.close()
