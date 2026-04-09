from __future__ import annotations

import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from .models import JobRecord
from .spiders.base import SpiderError, SpiderResult
from .spiders.jobspy_spider import JobspySpider
from .spiders.sce import SCESpider
from .spiders.turijobs import TurijobsSpider
from .utils import write_csv


CANARY_LOCATIONS = [
    "Canary Islands",
    "Islas Canarias",
    "Las Palmas",
    "Santa Cruz de Tenerife",
    "Tenerife",
    "Gran Canaria",
    "Lanzarote",
    "Fuerteventura",
    "La Palma",
    "Gomera",
    "El Hierro",
    "Las Palmas de Gran Canaria",
    "Santa Cruz de Tenerife",
    "San Cristóbal de La Laguna",
    "Arucas",
    "Puerto del Rosario",
    "San Bartolomé de Tirajana",
    "Adeje",
    "Granadilla de Abona",
    "Puerto de la Cruz",
    "Arona",
    "Santiago del Teide",
    "Los Cristianos",
    "Playa de las Américas",
    "Maspalomas",
    "Corralejo",
]


class ScalableJobspySpider:
    source = "jobspy"

    def __init__(self, max_runtime_seconds: int = 2700) -> None:
        self.max_runtime_seconds = max_runtime_seconds
        self.start_time = None
        self.records: list[JobRecord] = []
        self.errors: list[str] = []

    def _time_remaining(self) -> bool:
        if self.start_time is None:
            return True
        elapsed = time.time() - self.start_time
        return elapsed < self.max_runtime_seconds

    def fetch(self, limit: int) -> SpiderResult:
        from jobspy import scrape_jobs

        self.start_time = time.time()
        self.records = []
        target = min(limit, 2000)

        location = "Canary Islands, Spain"
        offset = 0
        batch_size = 100

        while len(self.records) < target and self._time_remaining():
            try:
                jobs = scrape_jobs(
                    site_name=["indeed"],
                    search_term="",
                    location=location,
                    results_wanted=batch_size,
                    country_indeed="spain",
                    offset=offset,
                    timeout_seconds=30,
                )

                if jobs is None or len(jobs) == 0:
                    break

                spider = JobspySpider()
                for _, row in jobs.iterrows():
                    if len(self.records) >= target or not self._time_remaining():
                        break
                    record = spider._convert_row_to_record(row)
                    if record:
                        self.records.append(record)

                offset += batch_size

                if len(jobs) < batch_size:
                    break

                delay = random.uniform(2, 5)
                time.sleep(delay)

            except Exception as exc:
                self.errors.append(str(exc))
                delay = random.uniform(5, 10)
                time.sleep(delay)
                continue

        if not self.records:
            raise SpiderError(f"No jobs scraped. Errors: {self.errors[:3]}")
        return SpiderResult(source=self.source, records=self.records[:limit])


def run_scaled(output_path: str, time_limit_minutes: int = 45, sce_only: bool = False) -> int:
    time_limit_seconds = time_limit_minutes * 60
    all_records: list[JobRecord] = []
    failures: list[str] = []

    start_total = time.time()

    print(f"[start] Scaling for {time_limit_minutes} minutes...")

    if sce_only:
        print("[start] SCE only mode")
        try:
            spider = SCESpider()
            result = spider.fetch(10000)
            all_records.extend(result.records)
            print(f"[ok] SCE: {len(result.records)} records")
        except SpiderError as exc:
            failures.append(f"SCE: {exc}")
            print(f"[skip] SCE: {exc}")
    else:
        spider_start = time.time()
        spider = ScalableJobspySpider(max_runtime_seconds=time_limit_seconds - 60)

        try:
            result = spider.fetch(5000)
            all_records.extend(result.records)
            spider_elapsed = time.time() - spider_start
            print(f"[ok] Indeed: {len(result.records)} records in {spider_elapsed:.1f}s")
        except SpiderError as exc:
            failures.append(f"JobSpy: {exc}")
            print(f"[skip] JobSpy: {exc}")

        if time.time() - start_total < time_limit_seconds - 60:
            remaining = time_limit_seconds - (time.time() - start_total)
            print(f"[start] Turijobs with {remaining:.0f}s remaining...")
            try:
                spider = TurijobsSpider()
                result = spider.fetch(500)
                all_records.extend(result.records)
                print(f"[ok] Turijobs: {len(result.records)} records")
            except SpiderError as exc:
                failures.append(f"Turijobs: {exc}")
                print(f"[skip] Turijobs: {exc}")

    total_elapsed = time.time() - start_total
    all_records.sort(key=lambda r: (r.source, r.publication_date or ""), reverse=True)
    written = write_csv(all_records, output_path)

    print(f"\n[done] {written} records in {total_elapsed:.1f}s ({total_elapsed/60:.1f} min)")
    print(f"[done] Wrote to {output_path}")

    if failures:
        print("\n[failures]")
        for failure in failures:
            print(f" - {failure}")

    return 0
