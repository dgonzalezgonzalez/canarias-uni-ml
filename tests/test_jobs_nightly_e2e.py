from src.canarias_uni_ml.jobs.models import JobRecord
from src.canarias_uni_ml.jobs.pipeline import run_jobs_pipeline
from src.canarias_uni_ml.jobs.spiders.base import SpiderError, SpiderResult
from src.canarias_uni_ml.jobs.storage import JobsRepository


def _record(*, external_id: str, title: str) -> JobRecord:
    return JobRecord(
        source="sce",
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
        source_url=f"https://example.org/{external_id}",
        scraped_at=JobRecord.now(),
    )


class StaticSpider:
    source = "sce"

    def __init__(self, records: list[JobRecord]) -> None:
        self.records = records

    def fetch(self, limit: int) -> SpiderResult:
        return SpiderResult(source=self.source, records=self.records[:limit])


class FlakySpider:
    source = "turijobs"

    def __init__(self, fail: bool) -> None:
        self.fail = fail

    def fetch(self, limit: int) -> SpiderResult:
        if self.fail:
            raise SpiderError("transient")
        return SpiderResult(source=self.source, records=[])


def test_nightly_two_cycles_update_without_duplicates(tmp_path):
    output = tmp_path / "jobs.csv"
    db = tmp_path / "jobs.db"

    assert (
        run_jobs_pipeline(
            limit_per_source=10,
            output_path=str(output),
            db_path=str(db),
            spiders=[StaticSpider([_record(external_id="1", title="v1"), _record(external_id="2", title="v1")])],
        )
        == 0
    )
    assert (
        run_jobs_pipeline(
            limit_per_source=10,
            output_path=str(output),
            db_path=str(db),
            spiders=[StaticSpider([_record(external_id="1", title="v2"), _record(external_id="2", title="v1")])],
        )
        == 0
    )

    records = JobsRepository(db).read_all()
    assert len(records) == 2
    by_id = {record.external_id: record for record in records}
    assert by_id["1"].title == "v2"
    assert by_id["2"].title == "v1"


def test_nightly_cycle_tolerates_one_source_error(tmp_path):
    output = tmp_path / "jobs.csv"
    db = tmp_path / "jobs.db"

    code = run_jobs_pipeline(
        limit_per_source=10,
        output_path=str(output),
        db_path=str(db),
        spiders=[StaticSpider([_record(external_id="1", title="v1")]), FlakySpider(fail=True)],
    )
    assert code == 0
    assert len(JobsRepository(db).read_all()) == 1
