from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from ..io import ensure_parent
from .models import SimilarityRecord


@dataclass(slots=True)
class AlignmentStats:
    inserted: int = 0
    updated: int = 0


class AlignmentRepository:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        ensure_parent(self.db_path)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS embedding_cache (
                    cache_key TEXT PRIMARY KEY,
                    text_hash TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    vector_json TEXT NOT NULL,
                    vector_dim INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS program_job_similarity (
                    pair_key TEXT PRIMARY KEY,
                    job_key TEXT NOT NULL,
                    degree_key TEXT NOT NULL,
                    score REAL NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    job_text_hash TEXT NOT NULL,
                    degree_text_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_similarity_job ON program_job_similarity(job_key)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_similarity_degree ON program_job_similarity(degree_key)")
            conn.commit()

    def get_cached_vector(self, cache_key: str) -> list[float] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT vector_json FROM embedding_cache WHERE cache_key = ?",
                (cache_key,),
            ).fetchone()
        if not row:
            return None
        return json.loads(row["vector_json"])

    def upsert_cached_vector(
        self,
        *,
        cache_key: str,
        text_hash: str,
        provider: str,
        model: str,
        vector: list[float],
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        vector_json = json.dumps(vector, separators=(",", ":"))
        with self._connect() as conn:
            existing = conn.execute(
                "SELECT cache_key FROM embedding_cache WHERE cache_key = ?",
                (cache_key,),
            ).fetchone()
            if existing is None:
                conn.execute(
                    """
                    INSERT INTO embedding_cache(
                        cache_key, text_hash, provider, model, vector_json, vector_dim, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (cache_key, text_hash, provider, model, vector_json, len(vector), now, now),
                )
            else:
                conn.execute(
                    """
                    UPDATE embedding_cache
                    SET text_hash = ?, provider = ?, model = ?, vector_json = ?, vector_dim = ?, updated_at = ?
                    WHERE cache_key = ?
                    """,
                    (text_hash, provider, model, vector_json, len(vector), now, cache_key),
                )
            conn.commit()

    def upsert_similarity(self, rows: list[SimilarityRecord]) -> AlignmentStats:
        now = datetime.now(timezone.utc).isoformat()
        stats = AlignmentStats()
        with self._connect() as conn:
            for row in rows:
                pair_key = f"{row.job_key}::{row.degree_key}::{row.provider}::{row.model}"
                existing = conn.execute(
                    "SELECT pair_key FROM program_job_similarity WHERE pair_key = ?",
                    (pair_key,),
                ).fetchone()
                if existing is None:
                    conn.execute(
                        """
                        INSERT INTO program_job_similarity(
                            pair_key, job_key, degree_key, score, provider, model,
                            job_text_hash, degree_text_hash, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            pair_key,
                            row.job_key,
                            row.degree_key,
                            row.score,
                            row.provider,
                            row.model,
                            row.job_text_hash,
                            row.degree_text_hash,
                            now,
                            now,
                        ),
                    )
                    stats.inserted += 1
                else:
                    conn.execute(
                        """
                        UPDATE program_job_similarity
                        SET score = ?, job_text_hash = ?, degree_text_hash = ?, updated_at = ?
                        WHERE pair_key = ?
                        """,
                        (row.score, row.job_text_hash, row.degree_text_hash, now, pair_key),
                    )
                    stats.updated += 1
            conn.commit()
        return stats
