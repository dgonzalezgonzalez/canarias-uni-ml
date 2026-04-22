from src.canarias_uni_ml.jobs.models import JobRecord
from src.canarias_uni_ml.jobs.pipeline import _select_with_source_coverage


def _record(source: str, idx: int) -> JobRecord:
    return JobRecord(
        source=source,
        external_id=str(idx),
        title=f"title-{idx}",
        company=None,
        description=None,
        salary_text=None,
        salary_min=None,
        salary_max=None,
        salary_currency=None,
        salary_period=None,
        publication_date=f"2026-04-{20+idx:02d}",
        update_date=None,
        source_url=f"https://example.org/{source}/{idx}",
        scraped_at=JobRecord.now(),
    )


def test_select_with_source_coverage_keeps_at_least_one_per_source():
    records = [
        _record("jobspy_indeed", 1),
        _record("jobspy_indeed", 2),
        _record("sce", 3),
        _record("sce", 4),
        _record("turijobs", 5),
        _record("turijobs", 6),
    ]
    selected = _select_with_source_coverage(records, 4)
    assert len(selected) == 4
    assert {record.source for record in selected} == {"jobspy_indeed", "sce", "turijobs"}
