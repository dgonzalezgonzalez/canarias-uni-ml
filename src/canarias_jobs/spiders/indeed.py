from __future__ import annotations

import asyncio
import re

from bs4 import BeautifulSoup

from ..models import JobRecord
from ..utils import clean_text
from .base import SpiderError, SpiderResult

try:
    from playwright.async_api import TimeoutError as PlaywrightTimeoutError
    from playwright.async_api import async_playwright
except ImportError:  # pragma: no cover
    async_playwright = None
    PlaywrightTimeoutError = Exception


INDEED_LIST_URL = "https://es.indeed.com/jobs?l=canarias&start={start}"


class IndeedSpider:
    source = "indeed"

    def fetch(self, limit: int) -> SpiderResult:
        if async_playwright is None:
            raise SpiderError("Indeed scraper requires playwright to be installed")
        records = asyncio.run(self._fetch_async(limit))
        if not records:
            raise SpiderError("Indeed returned no records")
        return SpiderResult(source=self.source, records=records)

    async def _fetch_async(self, limit: int) -> list[JobRecord]:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.set_extra_http_headers({"Accept-Language": "es-ES,es;q=0.9"})
            records: dict[str, JobRecord] = {}
            for start in range(0, limit, 10):
                await page.goto(INDEED_LIST_URL.format(start=start), wait_until="domcontentloaded")
                try:
                    await page.wait_for_selector("[data-jk], a[href*='viewjob?jk=']", timeout=15000)
                except PlaywrightTimeoutError as exc:
                    content = await page.content()
                    await browser.close()
                    raise SpiderError(
                        "Indeed did not expose job cards. Cloudflare likely blocked the session."
                    ) from exc
                listing_html = await page.content()
                jobs = self._extract_listing_jobs(listing_html)
                for job in jobs:
                    jk = job["external_id"]
                    if jk in records:
                        continue
                    detail = await self._fetch_detail(page, jk)
                    records[jk] = self._normalize_record(job, detail)
                    if len(records) >= limit:
                        break
                if len(records) >= limit:
                    break
            await browser.close()
            return list(records.values())[:limit]

    async def _fetch_detail(self, page, jk: str) -> dict[str, str | None]:
        detail_url = f"https://es.indeed.com/viewjob?jk={jk}"
        await page.goto(detail_url, wait_until="domcontentloaded")
        try:
            await page.wait_for_selector("body", timeout=10000)
        except PlaywrightTimeoutError as exc:
            raise SpiderError(f"Indeed detail page failed for jk={jk}") from exc
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text("\n", strip=True)
        detail = {
            "description": None,
            "salary_text": None,
            "contract_type": None,
            "workday": None,
            "schedule": None,
            "municipality": None,
            "province": None,
        }
        detail["description"] = clean_text(text)
        detail["salary_text"] = self._section_after(text, "Salario")
        detail["contract_type"] = self._section_after(text, "Tipo de empleo")
        detail["schedule"] = self._section_after(text, "Turno y horario")
        location = self._section_after(text, "Ubicación")
        if location:
            detail["municipality"], detail["province"] = self._split_location(location)
        return detail

    def _extract_listing_jobs(self, html: str) -> list[dict[str, str | None]]:
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select("[data-jk]")
        jobs = []
        for card in cards:
            jk = clean_text(card.get("data-jk"))
            if not jk:
                continue
            title = clean_text(card.get_text(" ", strip=True))
            href = None
            link = card.find("a", href=re.compile(r"viewjob\?jk="))
            if link:
                href = link.get("href")
                title = clean_text(link.get_text(" ", strip=True)) or title
            jobs.append(
                {
                    "external_id": jk,
                    "title": title or "Oferta Indeed",
                    "company": None,
                    "salary_text": None,
                    "publication_date": None,
                    "municipality": None,
                    "province": None,
                    "source_url": f"https://es.indeed.com/viewjob?jk={jk}",
                }
            )
        return jobs

    def _normalize_record(self, listing: dict[str, str | None], detail: dict[str, str | None]) -> JobRecord:
        municipality = detail.get("municipality") or listing.get("municipality")
        province = detail.get("province") or listing.get("province")
        return JobRecord(
            source=self.source,
            external_id=listing["external_id"] or "",
            title=listing["title"] or "Oferta Indeed",
            company=listing.get("company"),
            description=detail.get("description"),
            salary_text=detail.get("salary_text") or listing.get("salary_text"),
            salary_min=None,
            salary_max=None,
            salary_currency="EUR" if detail.get("salary_text") else None,
            salary_period=None,
            publication_date=listing.get("publication_date"),
            update_date=None,
            province=province,
            municipality=municipality,
            island=None,
            raw_location=clean_text(" / ".join(filter(None, [municipality, province]))),
            contract_type=detail.get("contract_type"),
            workday=detail.get("workday"),
            schedule=detail.get("schedule"),
            vacancies=None,
            source_url=listing.get("source_url") or f"https://es.indeed.com/viewjob?jk={listing['external_id']}",
            scraped_at=JobRecord.now(),
        )

    @staticmethod
    def _section_after(text: str, heading: str) -> str | None:
        if heading not in text:
            return None
        section = text.split(heading, 1)[1]
        lines = [line.strip() for line in section.splitlines() if line.strip()]
        if not lines:
            return None
        return clean_text(lines[0])

    @staticmethod
    def _split_location(location: str) -> tuple[str | None, str | None]:
        cleaned = clean_text(location) or ""
        if "," in cleaned:
            municipality, province = cleaned.split(",", 1)
            return clean_text(municipality), clean_text(province.replace("provincia", ""))
        return clean_text(cleaned), None
