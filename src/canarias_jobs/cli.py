from __future__ import annotations

import argparse
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from .models import JobRecord
from .scale import run_scaled
from .spiders import IndeedApiSpider, IndeedSpider, InfoJobsSpider, JobspySpider, SCESpider, SpiderError, TurijobsSpider
from .utils import write_csv


DEFAULT_OUTPUT = Path("data/processed/canarias_jobs.csv")
PROCESSED_DIR = Path("data/processed")


def run_merge(output_path: str) -> int:
    all_records: list[JobRecord] = []

    csv_files = sorted(PROCESSED_DIR.glob("*.csv"))

    if not csv_files:
        print("[skip] No CSV files found in data/processed/")
        return 1

    for csv_file in csv_files:
        with open(csv_file) as f:
            reader = csv.DictReader(f)
            for row in reader:
                record = JobRecord(**row)
                all_records.append(record)

    seen_urls: set[str] = set()
    unique_records: list[JobRecord] = []
    for r in all_records:
        if r.source_url not in seen_urls:
            seen_urls.add(r.source_url)
            unique_records.append(r)

    unique_records.sort(key=lambda r: (r.source, r.publication_date or ""), reverse=True)
    written = write_csv(unique_records, output_path)

    sources: dict[str, int] = {}
    for r in unique_records:
        src = r.source.split("_")[0]
        sources[src] = sources.get(src, 0) + 1

    print(f"[done] Merged {len(unique_records)} unique records from {len(csv_files)} files")
    for src, count in sorted(sources.items()):
        print(f"  {src}: {count}")
    print(f"[done] Wrote to {output_path}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape Canary Islands job postings.")
    parser.add_argument("--limit-per-source", type=int, default=50)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--scale", action="store_true", help="Scale mode: maximum jobs in time limit")
    parser.add_argument("--time-limit", type=int, default=45, help="Time limit in minutes for scale mode")
    parser.add_argument("--sce-only", action="store_true", help="Only scrape SCE (fast API)")
    parser.add_argument("--merge", action="store_true", help="Merge all existing CSV files in data/processed/")
    return parser.parse_args()


def run() -> int:
    args = parse_args()

    if args.merge:
        return run_merge(args.output)

    if args.scale:
        return run_scaled(
            output_path=args.output,
            time_limit_minutes=args.time_limit,
            sce_only=args.sce_only,
        )

    spiders = [SCESpider(), TurijobsSpider(), IndeedApiSpider(), IndeedSpider(), InfoJobsSpider(), JobspySpider()]
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
