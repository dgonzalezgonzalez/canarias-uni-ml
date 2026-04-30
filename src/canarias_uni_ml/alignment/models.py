from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class EmbeddingCacheRecord:
    cache_key: str
    text_hash: str
    provider: str
    model: str
    vector: list[float]


@dataclass(slots=True)
class SimilarityRecord:
    job_key: str
    degree_key: str
    score: float
    provider: str
    model: str
    job_text_hash: str
    degree_text_hash: str
