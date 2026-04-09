from __future__ import annotations

import json
import os
import re
from typing import Any

import httpx

from ..models import JobRecord
from ..utils import clean_text
from .base import SpiderError, SpiderResult


INDEED_SEARCH_URL = "https://es.indeed.com/jobs"
INDEED_DETAIL_URL = "https://es.indeed.com/m/basecamp/viewjob?viewtype=embedded&jk={jobkey}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}

MOSAIC_PATTERN = re.compile(
    r'window\.mosaic\.providerData\["mosaic-provider-jobcards"\]\s*=\s*(\{[\s\S]*?\});',
)


class IndeedApiSpider:
    source = "indeed"

    def __init__(self) -> None:
        self.session = httpx.Client(timeout=30.0, headers=HEADERS, follow_redirects=True)
        self.scrapingbee_key = os.getenv("SCRAPINGBEE_API_KEY")

    def fetch(self, limit: int) -> SpiderResult:
        records = self._fetch_jobs(limit)
        if not records:
            raise SpiderError("Indeed returned no records. Cloudflare may be blocking requests.")
        return SpiderResult(source=self.source, records=records)

    def _fetch_jobs(self, limit: int) -> list[JobRecord]:
        records: dict[str, JobRecord] = {}
        offset = 0
        max_offset = min(limit * 2, 200)

        while offset < max_offset and len(records) < limit:
            jobs = self._fetch_page(offset)
            if not jobs:
                break
            for job in jobs:
                jk = job.get("jobkey", "")
                if not jk or jk in records:
                    continue
                records[jk] = self._normalize_job(job)
                if len(records) >= limit:
                    break
            offset += 10

        return list(records.values())[:limit]

    def _fetch_page(self, offset: int) -> list[dict[str, Any]]:
        params = {
            "q": "",
            "l": "canarias",
            "vjk": "",
            "filter": "0",
            "start": str(offset),
        }

        if self.scrapingbee_key:
            return self._fetch_with_scrapingbee(params)
        return self._fetch_direct(params)

    def _fetch_direct(self, params: dict[str, str]) -> list[dict[str, Any]]:
        response = self.session.get(INDEED_SEARCH_URL, params=params)
        if response.status_code == 403:
            raise SpiderError("Indeed blocked request (403). Cloudflare protection active.")
        if response.status_code != 200:
            raise SpiderError(f"Indeed returned status {response.status_code}")
        return self._extract_jobs(response.text)

    def _fetch_with_scrapingbee(self, params: dict[str, str]) -> list[dict[str, Any]]:
        url = f"{INDEED_SEARCH_URL}?q={params['q']}&l={params['l']}&start={params['start']}"
        sb_url = "https://app.scrapingbee.com/api/v1/"
        sb_params = {
            "api_key": self.scrapingbee_key,
            "url": url,
            "render_js": "true",
            "country_code": "es",
        }
        response = self.session.get(sb_url, params=sb_params)
        if response.status_code != 200:
            raise SpiderError(f"ScrapingBee error: {response.status_code}")
        return self._extract_jobs(response.text)

    def _extract_jobs(self, html: str) -> list[dict[str, Any]]:
        match = MOSAIC_PATTERN.search(html)
        if not match:
            return []
        try:
            data = json.loads(match.group(1))
            results = data.get("metaData", {}).get("mosaicProviderJobCardsModel", {}).get("results", [])
            return results
        except json.JSONDecodeError:
            return []

    def _normalize_job(self, job: dict[str, Any]) -> JobRecord:
        location = clean_text(job.get("formattedLocation", "")) or ""
        salary = clean_text(job.get("salary") or job.get("estimatedSalary") or "")
        date_str = job.get("date", "")
        company = clean_text(job.get("companyName") or job.get("company") or "")

        municipality = None
        province = "Las Palmas"
        if "," in location:
            parts = location.split(",", 1)
            municipality = clean_text(parts[0])
            province_part = clean_text(parts[1])
            if province_part:
                province = province_part

        return JobRecord(
            source=self.source,
            external_id=job.get("jobkey", ""),
            title=clean_text(job.get("title", "Oferta Indeed")),
            company=company,
            description=None,
            salary_text=salary,
            salary_min=None,
            salary_max=None,
            salary_currency="EUR" if salary else None,
            salary_period=None,
            publication_date=self._parse_date(date_str),
            update_date=None,
            province=province,
            municipality=municipality,
            island=None,
            raw_location=location,
            contract_type=None,
            workday=None,
            schedule=None,
            vacancies=None,
            source_url=f"https://es.indeed.com/viewjob?jk={job.get('jobkey', '')}",
            scraped_at=JobRecord.now(),
        )

    @staticmethod
    def _parse_date(date_str: str) -> str | None:
        if not date_str:
            return None
        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(date_str)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            return None
