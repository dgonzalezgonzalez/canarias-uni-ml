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
        job_title="Job A",
        degree_title="Degree B",
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


def test_similarity_export_csv(tmp_path):
    repo = AlignmentRepository(tmp_path / "alignment.db")
    row = SimilarityRecord(
        job_key="job::a::1",
        degree_key="degree::b::1",
        job_title="Job A",
        degree_title="Degree B",
        score=0.9,
        provider="ollama",
        model="nomic-embed-text",
        job_text_hash="jh",
        degree_text_hash="dh",
    )
    repo.upsert_similarity([row])
    written = repo.export_similarity_csv(tmp_path / "program_job_similarity.csv")
    assert written == 1
    content = (tmp_path / "program_job_similarity.csv").read_text(encoding="utf-8")
    assert "pair_key,job_key,degree_key,job_title,degree_title,score,provider,model" in content
    assert "job::a::1" in content
    assert "Job A" in content
    assert "Degree B" in content


def test_delete_missing_similarity_pairs(tmp_path):
    repo = AlignmentRepository(tmp_path / "alignment.db")
    row1 = SimilarityRecord(
        job_key="job::a::1",
        degree_key="degree::b::1",
        job_title="Job A",
        degree_title="Degree B",
        score=0.9,
        provider="ollama",
        model="nomic-embed-text",
        job_text_hash="jh1",
        degree_text_hash="dh1",
    )
    row2 = SimilarityRecord(
        job_key="job::a::2",
        degree_key="degree::b::2",
        job_title="Job C",
        degree_title="Degree D",
        score=0.8,
        provider="ollama",
        model="nomic-embed-text",
        job_text_hash="jh2",
        degree_text_hash="dh2",
    )
    repo.upsert_similarity([row1, row2])
    keep = {f"{row1.job_key}::{row1.degree_key}::{row1.provider}::{row1.model}"}
    removed = repo.delete_missing_similarity_pairs(
        provider="ollama",
        model="nomic-embed-text",
        keep_pair_keys=keep,
    )
    assert removed == 1
    written = repo.export_similarity_csv(tmp_path / "out.csv")
    assert written == 1
