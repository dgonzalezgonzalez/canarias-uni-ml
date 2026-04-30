from src.canarias_uni_ml.jobs.models import JobRecord
from src.canarias_uni_ml.jobs.storage import JobsRepository, canonical_job_key


def _record(
    *,
    source: str = "sce",
    external_id: str = "1",
    source_url: str = "https://example.org/jobs/1",
    title: str = "title-1",
) -> JobRecord:
    return JobRecord(
        source=source,
        external_id=external_id,
        title=title,
        company="Acme",
        description="desc",
        salary_text=None,
        salary_min=None,
        salary_max=None,
        salary_currency=None,
        salary_period=None,
        publication_date="2026-04-22T00:00:00+00:00",
        update_date=None,
        source_url=source_url,
        scraped_at=JobRecord.now(),
    )


def test_jobs_repository_insert_update_unchanged(tmp_path):
    repo = JobsRepository(tmp_path / "jobs.db")

    inserted = repo.upsert_records([_record(title="title-v1")])
    assert inserted.inserted == 1
    assert inserted.updated == 0
    assert inserted.unchanged == 0

    unchanged = repo.upsert_records([_record(title="title-v1")])
    assert unchanged.inserted == 0
    assert unchanged.updated == 0
    assert unchanged.unchanged == 1

    updated = repo.upsert_records([_record(title="title-v2")])
    assert updated.inserted == 0
    assert updated.updated == 1
    assert updated.unchanged == 0

    output = tmp_path / "jobs.csv"
    written = repo.export_csv(output)
    assert written == 1
    content = output.read_text(encoding="utf-8")
    assert "title-v2" in content


def test_jobs_repository_uses_source_url_when_external_id_missing(tmp_path):
    repo = JobsRepository(tmp_path / "jobs.db")
    record = _record(external_id="", source_url="https://example.org/jobs/same")
    stats = repo.upsert_records([record, record])
    assert stats.inserted == 1
    assert stats.unchanged == 1


def test_canonical_job_key_requires_identity_fields():
    record = _record(external_id="", source_url="", title="")
    record.company = None
    record.publication_date = None
    record.raw_location = None
    try:
        canonical_job_key(record)
        assert False, "expected ValueError"
    except ValueError:
        assert True
