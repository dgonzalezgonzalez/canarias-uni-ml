from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass, fields
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from ..io import ensure_parent, write_csv_rows
from .models import JobRecord
from .utils import clean_text

JOB_FIELDS = tuple(field.name for field in fields(JobRecord))
VOLATILE_HASH_FIELDS = {"scraped_at"}


@dataclass(slots=True)
class UpsertStats:
    inserted: int = 0
    updated: int = 0
    unchanged: int = 0


def canonical_job_key(record: JobRecord) -> str:
    source = clean_text(record.source) or "unknown"
    external_id = clean_text(record.external_id)
    if external_id:
        return f"id::{source.lower()}::{external_id}"

    source_url = (clean_text(record.source_url) or "").lower()
    if source_url:
        return f"url::{source_url}"

    title = clean_text(record.title)
    company = clean_text(record.company)
    publication_date = clean_text(record.publication_date)
    location = clean_text(record.raw_location or record.municipality or record.island or record.province)
    if not any((title, company, publication_date, location)):
        raise ValueError("Job record has no stable identity fields")
    return "row::{source}::{title}::{company}::{date}::{location}".format(
        source=source.lower(),
        title=title or "",
        company=company or "",
        date=publication_date or "",
        location=location or "",
    )


def payload_hash(record: JobRecord) -> str:
    payload = {
        key: value
        for key, value in record.to_row().items()
        if key not in VOLATILE_HASH_FIELDS
    }
    serialized = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class JobsRepository:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        ensure_parent(self.db_path)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        column_defs = ", ".join(f'"{name}" TEXT' for name in JOB_FIELDS)
        with self._connect() as conn:
            conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS jobs (
                    job_key TEXT PRIMARY KEY,
                    {column_defs},
                    payload_hash TEXT NOT NULL,
                    first_seen_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source)")
            conn.commit()

    def upsert_records(self, records: Iterable[JobRecord]) -> UpsertStats:
        stats = UpsertStats()
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            for record in records:
                key = canonical_job_key(record)
                record_hash = payload_hash(record)
                existing = conn.execute(
                    "SELECT payload_hash FROM jobs WHERE job_key = ?",
                    (key,),
                ).fetchone()
                row = record.to_row()
                if existing is None:
                    self._insert(conn=conn, job_key=key, row=row, row_hash=record_hash, now=now)
                    stats.inserted += 1
                    continue

                if existing["payload_hash"] == record_hash:
                    conn.execute(
                        "UPDATE jobs SET last_seen_at = ? WHERE job_key = ?",
                        (now, key),
                    )
                    stats.unchanged += 1
                    continue

                self._update(conn=conn, job_key=key, row=row, row_hash=record_hash, now=now)
                stats.updated += 1
            conn.commit()
        return stats

    def export_csv(self, output_path: str | Path) -> int:
        query = f"""
            SELECT {", ".join(f'"{name}"' for name in JOB_FIELDS)}
            FROM jobs
            ORDER BY COALESCE(publication_date, '') DESC, source ASC
        """
        with self._connect() as conn:
            rows = conn.execute(query).fetchall()
        records = [JobRecord(**{name: row[name] for name in JOB_FIELDS}) for row in rows]
        return write_csv_rows(records, output_path)

    def read_all(self) -> list[JobRecord]:
        query = f"""
            SELECT {", ".join(f'"{name}"' for name in JOB_FIELDS)}
            FROM jobs
            ORDER BY source ASC, title ASC
        """
        with self._connect() as conn:
            rows = conn.execute(query).fetchall()
        return [JobRecord(**{name: row[name] for name in JOB_FIELDS}) for row in rows]

    def _insert(
        self,
        *,
        conn: sqlite3.Connection,
        job_key: str,
        row: dict[str, str | None],
        row_hash: str,
        now: str,
    ) -> None:
        columns = ("job_key", *JOB_FIELDS, "payload_hash", "first_seen_at", "last_seen_at", "updated_at")
        placeholders = ", ".join("?" for _ in columns)
        quoted_columns = ", ".join(f'"{column}"' for column in columns)
        conn.execute(
            f"INSERT INTO jobs ({quoted_columns}) VALUES ({placeholders})",
            (job_key, *[row.get(name) for name in JOB_FIELDS], row_hash, now, now, now),
        )

    def _update(
        self,
        *,
        conn: sqlite3.Connection,
        job_key: str,
        row: dict[str, str | None],
        row_hash: str,
        now: str,
    ) -> None:
        assignments = ", ".join(f'"{name}" = ?' for name in JOB_FIELDS)
        conn.execute(
            f"""
            UPDATE jobs
            SET {assignments},
                payload_hash = ?,
                last_seen_at = ?,
                updated_at = ?
            WHERE job_key = ?
            """,
            (*[row.get(name) for name in JOB_FIELDS], row_hash, now, now, job_key),
        )
