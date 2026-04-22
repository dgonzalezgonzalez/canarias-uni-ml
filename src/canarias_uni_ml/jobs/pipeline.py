from __future__ import annotations

import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from ..io import write_csv_rows
from .models import JobRecord
from .scale import run_scaled
from .spiders import JobspySpider, SCESpider, SpiderError, TurijobsSpider

PROCESSED_DIR = Path("data/processed")


def run_jobs_merge(output_path: str) -> int:
    all_records: list[JobRecord] = []
    csv_files = sorted(PROCESSED_DIR.glob("*.csv"))
    if not csv_files:
        print("[skip] No CSV files found in data/processed/")
        return 1
    for csv_file in csv_files:
        with open(csv_file, encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            all_records.extend(JobRecord(**row) for row in reader)
    seen_urls: set[str] = set()
    unique_records: list[JobRecord] = []
    for record in all_records:
        if record.source_url not in seen_urls:
            seen_urls.add(record.source_url)
            unique_records.append(record)
    unique_records.sort(key=lambda r: (r.source, r.publication_date or ""), reverse=True)
    written = write_csv_rows(unique_records, output_path)
    print(f"[done] wrote {written} merged rows to {output_path}")
    return 0


def run_jobs_pipeline(limit_per_source: int, output_path: str) -> int:
    spiders = [SCESpider(), TurijobsSpider(), JobspySpider()]
    all_records: list[JobRecord] = []
    failures: list[str] = []

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(spider.fetch, limit_per_source): spider.source for spider in spiders}
        for future in as_completed(futures):
            source = futures[future]
            try:
                result = future.result()
                all_records.extend(result.records)
                print(f"[ok] {source}: {len(result.records)} records")
            except SpiderError as exc:
                failures.append(f"{source}: {exc}")
                print(f"[skip] {source}: {exc}")
            except Exception as exc:  # pragma: no cover
                failures.append(f"{source}: {exc}")
                print(f"[error] {source}: {exc}")

    all_records.sort(key=lambda record: (record.source, record.publication_date or ""), reverse=True)
    written = write_csv_rows(all_records, output_path)
    print(f"[done] wrote {written} rows to {output_path}")
    if failures:
        print("[failures]")
        for failure in failures:
            print(f" - {failure}")
    return 0


def run_jobs_scale(**kwargs) -> int:
    return run_scaled(**kwargs)
