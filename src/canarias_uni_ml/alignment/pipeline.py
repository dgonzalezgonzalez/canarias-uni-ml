from __future__ import annotations

import csv

from ..config import Settings
from ..embeddings.pipeline import embed_with_cache, text_hash
from .models import SimilarityRecord
from .pairing import build_candidate_pairs
from .similarity import cosine_similarity
from .storage import AlignmentRepository


def _read_csv(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def run_alignment_pipeline(
    *,
    jobs_csv_path: str,
    degrees_csv_path: str,
    db_path: str,
    provider_name: str,
    model: str | None,
    settings: Settings,
    min_text_len: int = 40,
) -> int:
    jobs = _read_csv(jobs_csv_path)
    degrees = _read_csv(degrees_csv_path)
    pairs = build_candidate_pairs(jobs, degrees, min_text_len=min_text_len)

    active_model = model or (
        "text-embedding-3-small" if provider_name == "openai" else settings.ollama_embedding_model
        if provider_name == "ollama"
        else "unknown-groq-embedding-model"
    )

    repo = AlignmentRepository(db_path)

    unique_texts: list[str] = []
    seen: set[str] = set()
    for pair in pairs:
        if pair.job_text not in seen:
            seen.add(pair.job_text)
            unique_texts.append(pair.job_text)
        if pair.degree_text not in seen:
            seen.add(pair.degree_text)
            unique_texts.append(pair.degree_text)

    vectors, _ = embed_with_cache(
        unique_texts,
        provider_name=provider_name,
        model=active_model,
        settings=settings,
        repo=repo,
    )
    vector_by_text = {text: vector for text, vector in zip(unique_texts, vectors)}

    rows: list[SimilarityRecord] = []
    for pair in pairs:
        left = vector_by_text.get(pair.job_text, [])
        right = vector_by_text.get(pair.degree_text, [])
        if not left or not right or len(left) != len(right):
            continue
        rows.append(
            SimilarityRecord(
                job_key=pair.job_key,
                degree_key=pair.degree_key,
                score=cosine_similarity(left, right),
                provider=provider_name,
                model=active_model,
                job_text_hash=text_hash(pair.job_text),
                degree_text_hash=text_hash(pair.degree_text),
            )
        )

    stats = repo.upsert_similarity(rows)
    print(
        "[done] alignment pairs={pairs} stored={stored} inserted={inserted} updated={updated}".format(
            pairs=len(pairs),
            stored=len(rows),
            inserted=stats.inserted,
            updated=stats.updated,
        )
    )
    return 0
