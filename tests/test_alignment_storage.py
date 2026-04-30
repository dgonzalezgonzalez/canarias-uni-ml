from src.canarias_uni_ml.alignment.models import SimilarityRecord
from src.canarias_uni_ml.alignment.storage import AlignmentRepository


def test_alignment_schema_and_cache_upsert(tmp_path):
    repo = AlignmentRepository(tmp_path / "alignment.db")

    key = "k1"
    assert repo.get_cached_vector(key) is None
    repo.upsert_cached_vector(
        cache_key=key,
        text_hash="h1",
        provider="ollama",
        model="nomic-embed-text",
        vector=[0.1, 0.2, 0.3],
    )
    assert repo.get_cached_vector(key) == [0.1, 0.2, 0.3]

    repo.upsert_cached_vector(
        cache_key=key,
        text_hash="h1",
        provider="ollama",
        model="nomic-embed-text",
        vector=[0.5, 0.6, 0.7],
    )
    assert repo.get_cached_vector(key) == [0.5, 0.6, 0.7]


def test_similarity_upsert_insert_then_update(tmp_path):
    repo = AlignmentRepository(tmp_path / "alignment.db")
    row = SimilarityRecord(
        job_key="job::a::1",
        degree_key="degree::b::1",
        score=0.5,
        provider="ollama",
        model="nomic-embed-text",
        job_text_hash="jh",
        degree_text_hash="dh",
    )
    first = repo.upsert_similarity([row])
    assert first.inserted == 1
    assert first.updated == 0

    row.score = 0.8
    second = repo.upsert_similarity([row])
    assert second.inserted == 0
    assert second.updated == 1
