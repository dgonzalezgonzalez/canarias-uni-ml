from __future__ import annotations

import asyncio
import json
import os
import re
from typing import Any

import httpx

from ..models import JobRecord
from ..utils import clean_text
from .base import SpiderError, SpiderResult


INDEED_SEARCH_URL = "https://es.indeed.com/jobs"
INDEED_DETAIL_URL = "https://es.indeed.com/viewjob?jk={jobkey}"

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
}

MOSAIC_PATTERN = re.compile(
    r'window\.mosaic\.providerData\["mosaic-provider-jobcards"\]\s*=\s*(\{[\s\S]*?\});',
)


class IndeedApiSpider:
    source = "indeed"

    def __init__(self) -> None:
        self.session = httpx.Client(timeout=30.0, headers=HEADERS, follow_redirects=True)
        self.scrapingbee_key = os.getenv("SCRAPINGBEE_API_KEY")
        self._playwright = None

    def fetch(self, limit: int) -> SpiderResult:
        if self.scrapingbee_key:
            try:
                records = self._fetch_with_playwright(limit)
                if records:
                    return SpiderResult(source=self.source, records=records)
            except Exception:
                pass
        
        records = self._fetch_with_scrapingbee_fallback(limit)
        if not records:
            raise SpiderError("Indeed returned no records. Cloudflare may be blocking requests.")
        return SpiderResult(source=self.source, records=records)

    def _fetch_with_playwright(self, limit: int) -> list[JobRecord]:
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            return []
        
        return asyncio.run(self._fetch_with_playwright_async(limit))

    async def _fetch_with_playwright_async(self, limit: int) -> list[JobRecord]:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.set_extra_http_headers({"Accept-Language": "es-ES,es;q=0.9"})
            
            records: list[JobRecord] = []
            offset = 0
            
            while len(records) < limit:
                await page.goto(
                    f"{INDEED_SEARCH_URL}?q=&l=Canarias&start={offset}",
                    wait_until="domcontentloaded",
                )
                
                await page.wait_for_timeout(2000)
                
                html = await page.content()
                jobs = self._extract_jobs(html)
                
                if not jobs:
                    break
                
                for job in jobs:
                    if len(records) >= limit:
                        break
                    
                    jk = job.get("jobkey", "")
                    if not jk:
                        continue
                    
                    detail = await self._fetch_detail_with_playwright(page, jk)
                    record = self._normalize_job(job, detail)
                    records.append(record)
                
                offset += 10
            
            await browser.close()
            return records

    async def _fetch_detail_with_playwright(self, page, jobkey: str) -> dict[str, Any]:
        detail_url = INDEED_DETAIL_URL.format(jobkey=jobkey)
        await page.goto(detail_url, wait_until="domcontentloaded")
        await page.wait_for_timeout(1000)
        
        html = await page.content()
        return self._extract_detail(html)

    def _fetch_with_scrapingbee_fallback(self, limit: int) -> list[JobRecord]:
        sb_url = "https://app.scrapingbee.com/api/v1/"
        
        all_jobs: list[dict[str, Any]] = []
        offset = 0
        
        while len(all_jobs) < limit:
            url = f"{INDEED_SEARCH_URL}?q=&l=Canarias&start={offset}"
            sb_params = {
                "api_key": self.scrapingbee_key,
                "url": url,
                "render_js": "true",
                "country_code": "es",
            }
            
            response = self.session.get(sb_url, params=sb_params, timeout=60)
            if response.status_code != 200:
                break
            
            jobs = self._extract_jobs(response.text)
            if not jobs:
                break
            
            all_jobs.extend(jobs)
            offset += 10
        
        records: list[JobRecord] = []
        for job in all_jobs[:limit]:
            jk = job.get("jobkey", "")
            if not jk:
                continue
            
            detail_url = INDEED_DETAIL_URL.format(jobkey=jk)
            sb_params = {
                "api_key": self.scrapingbee_key,
                "url": detail_url,
                "render_js": "true",
                "country_code": "es",
            }
            
            try:
                detail_response = self.session.get(sb_url, params=sb_params, timeout=60)
                if detail_response.status_code == 200:
                    detail = self._extract_detail(detail_response.text)
                else:
                    detail = {}
            except Exception:
                detail = {}
            
            record = self._normalize_job(job, detail)
            records.append(record)
        
        return records

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

    def _extract_detail(self, html: str) -> dict[str, Any]:
        from bs4 import BeautifulSoup
        
        detail = {
            "description": None,
            "salary_text": None,
            "contract_type": None,
            "workday": None,
            "schedule": None,
        }
        
        soup = BeautifulSoup(html, "html.parser")
        
        desc_elem = soup.find("div", id="jobDescriptionText")
        if desc_elem:
            text = desc_elem.get_text(" ", strip=True)
            if len(text) > 50:
                detail["description"] = clean_text(text)
        
        if not detail["description"]:
            desc_elem = soup.find(["div", "section"], class_=re.compile(r"description|jobsearch.*description", re.I))
            if desc_elem:
                text = desc_elem.get_text(" ", strip=True)
                if len(text) > 50:
                    detail["description"] = clean_text(text)
        
        salary_elem = soup.find(["span", "div"], class_=re.compile(r"salary|estimated", re.I))
        if salary_elem:
            text = salary_elem.get_text(" ", strip=True)
            if text and len(text) > 2:
                detail["salary_text"] = clean_text(text)
        
        insights = soup.find_all(["div", "section"], class_=re.compile(r"insights|match-insights", re.I))
        for section in insights:
            h3 = section.find("h3")
            if h3:
                text = h3.get_text(" ", strip=True).lower()
                if "empleo" in text and not detail["contract_type"]:
                    items = section.find_all("span")
                    for item in items:
                        item_text = item.get_text(" ", strip=True)
                        if item_text and len(item_text) > 2:
                            detail["contract_type"] = clean_text(item_text)
                            break
                elif "horario" in text and not detail["schedule"]:
                    items = section.find_all("span")
                    for item in items:
                        item_text = item.get_text(" ", strip=True)
                        if item_text and len(item_text) > 2:
                            if not detail["schedule"]:
                                detail["schedule"] = clean_text(item_text)
                            else:
                                detail["schedule"] += f", {clean_text(item_text)}"
        
        for label, field in [
            ("Salario", "salary_text"),
            ("Tipo de empleo", "contract_type"),
            ("Tipo de jornada", "workday"),
            ("Turno y horario", "schedule"),
        ]:
            pattern = re.compile(rf"{label}[:\s]*(.+?)(?:\n|<)", re.I)
            match = pattern.search(html)
            if match:
                value = clean_text(match.group(1))
                if value and len(value) > 1:
                    if not detail[field]:
                        detail[field] = value
        
        if not detail["description"]:
            for elem_id in ["jobDescription", "jobDetails", "job-content"]:
                elem = soup.find(id=re.compile(elem_id, re.I))
                if elem:
                    text = elem.get_text(" ", strip=True)
                    if len(text) > 100:
                        detail["description"] = clean_text(text[:5000])
                        break
        
        return detail

    def _normalize_job(self, job: dict[str, Any], detail: dict[str, Any]) -> JobRecord:
        location = clean_text(job.get("formattedLocation", "")) or ""
        salary = detail.get("salary_text") or clean_text(job.get("salary") or job.get("estimatedSalary") or "")
        date_str = job.get("date", "")
        company = clean_text(job.get("companyName") or job.get("company") or "")
        description = detail.get("description")

        municipality = None
        province = "Las Palmas"
        if "," in location:
            parts = location.split(",", 1)
            municipality = clean_text(parts[0])
            province_part = clean_text(parts[1])
            if province_part:
                province = province_part
        elif location:
            municipality = location

        return JobRecord(
            source=self.source,
            external_id=job.get("jobkey", ""),
            title=clean_text(job.get("title", "Oferta Indeed")),
            company=company,
            description=description,
            salary_text=salary if salary else None,
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
            contract_type=detail.get("contract_type"),
            workday=detail.get("workday"),
            schedule=detail.get("schedule"),
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
