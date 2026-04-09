from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .models import JobRecord
from .spiders import IndeedApiSpider, IndeedSpider, InfoJobsSpider, SCESpider, SpiderError, TurijobsSpider
from .utils import write_csv


DEFAULT_OUTPUT = Path("data/processed/canarias_jobs.csv")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape Canary Islands job postings.")
    parser.add_argument("--limit-per-source", type=int, default=50)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    return parser.parse_args()


def run() -> int:
    args = parse_args()
    spiders = [SCESpider(), TurijobsSpider(), IndeedApiSpider(), IndeedSpider(), InfoJobsSpider()]
    all_records: list[JobRecord] = []
    failures: list[str] = []

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(spider.fetch, args.limit_per_source): spider.source for spider in spiders
        }
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
    written = write_csv(all_records, args.output)
    print(f"[done] wrote {written} rows to {args.output}")
    if failures:
        print("[failures]")
        for failure in failures:
            print(f" - {failure}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
