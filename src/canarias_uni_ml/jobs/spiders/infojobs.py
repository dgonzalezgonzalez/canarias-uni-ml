from __future__ import annotations

import base64
import os

import requests

from ..models import JobRecord
from ..utils import clean_text, parse_date
from .base import SpiderError, SpiderResult


INFOJOBS_API = "https://api.infojobs.net/api/9/offer"
INFOJOBS_LIST_URL_LAS_PALMAS = "https://www.infojobs.net/ofertas-trabajo?provinceIds=20"
INFOJOBS_LIST_URL_TENERIFE = "https://www.infojobs.net/ofertas-trabajo?provinceIds=46"


class InfoJobsSpider:
    source = "infojobs"

    def __init__(self) -> None:
        self.client_id = os.getenv("INFOJOBS_CLIENT_ID")
        self.client_secret = os.getenv("INFOJOBS_CLIENT_SECRET")
        self.scrapingbee_key = os.getenv("SCRAPINGBEE_API_KEY")
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0", "Accept": "application/json"})

    def fetch(self, limit: int) -> SpiderResult:
        if self.client_id and self.client_secret:
            return self._fetch_via_api(limit)
        elif self.scrapingbee_key:
            return self._fetch_via_scrapingbee(limit)
        else:
            raise SpiderError(
                "InfoJobs requires either INFOJOBS_CLIENT_ID/INFOJOBS_CLIENT_SECRET "
                "or SCRAPINGBEE_API_KEY"
            )

    def _fetch_via_api(self, limit: int) -> SpiderResult:
        offers = self._fetch_list(limit)
        records = [self._fetch_detail(offer["id"]) for offer in offers[:limit]]
        return SpiderResult(source=self.source, records=records)

    def _fetch_via_scrapingbee(self, limit: int) -> SpiderResult:
        import re
        from bs4 import BeautifulSoup
        
        records: list[JobRecord] = []
        
        for province_url in [INFOJOBS_LIST_URL_LAS_PALMAS, INFOJOBS_LIST_URL_TENERIFE]:
            if len(records) >= limit:
                break
            
            sb_url = "https://app.scrapingbee.com/api/v1/"
            sb_params = {
                "api_key": self.scrapingbee_key,
                "url": province_url,
                "render_js": "true",
                "country_code": "es",
            }
            
            response = self.session.get(sb_url, params=sb_params, timeout=60)
            if response.status_code != 200:
                continue
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            for link in soup.find_all("a", href=re.compile(r"/ofertas-trabajo/[^/]+/[^.]+\.[a-z0-9]+", re.IGNORECASE)):
                if len(records) >= limit:
                    break
                
                href = link.get("href", "")
                if not href.startswith("http"):
                    href = f"https://www.infojobs.net{href}"
                
                offer_id = href.split("/")[-1].split(".")[-1]
                
                parent = link.find_parent("article") or link.find_parent("li") or link.find_parent("div")
                title = clean_text(link.get_text())
                if not title:
                    continue
                
                company = None
                salary = None
                location = None
                
                if parent:
                    company_elem = parent.find(class_=re.compile(r"company", re.IGNORECASE))
                    if company_elem:
                        company = clean_text(company_elem.get_text())
                    
                    salary_elem = parent.find(class_=re.compile(r"salary", re.IGNORECASE))
                    if salary_elem:
                        salary = clean_text(salary_elem.get_text())
                    
                    location_elem = parent.find(class_=re.compile(r"location", re.IGNORECASE))
                    if location_elem:
                        location = clean_text(location_elem.get_text())
                
                province = None
                municipality = None
                if location:
                    if any(x in location.lower() for x in ["las palmas", "gran canaria", "lanzarote", "fuerteventura"]):
                        province = "Las Palmas"
                        municipality = location.split(",")[0].strip() if "," in location else location
                    elif any(x in location.lower() for x in ["tenerife", "santa cruz", "la palma", "la gomera"]):
                        province = "Santa Cruz de Tenerife"
                        municipality = location.split(",")[0].strip() if "," in location else location
                
                records.append(JobRecord(
                    source=self.source,
                    external_id=offer_id,
                    title=title,
                    company=company,
                    description=None,
                    salary_text=salary,
                    salary_min=None,
                    salary_max=None,
                    salary_currency="EUR" if salary else None,
                    salary_period=None,
                    publication_date=None,
                    update_date=None,
                    province=province,
                    municipality=municipality,
                    island=None,
                    raw_location=location,
                    contract_type=None,
                    workday=None,
                    schedule=None,
                    vacancies=None,
                    source_url=href,
                    scraped_at=JobRecord.now(),
                ))
        
        if not records:
            raise SpiderError("InfoJobs returned no records via ScrapingBee")
        
        return SpiderResult(source=self.source, records=records)

    def _auth_headers(self) -> dict[str, str]:
        credentials = f"{self.client_id}:{self.client_secret}".encode()
        token = base64.b64encode(credentials).decode()
        return {"Authorization": f"Basic {token}"}

    def _fetch_list(self, limit: int) -> list[dict]:
        response = self.session.get(
            INFOJOBS_API,
            headers=self._auth_headers(),
            params=[
                ("province", "las-palmas"),
                ("province", "santa-cruz-de-tenerife"),
                ("page", "1"),
                ("maxResults", str(limit)),
                ("order", "updated-desc"),
            ],
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        return payload.get("items", payload)

    def _fetch_detail(self, offer_id: str) -> JobRecord:
        response = self.session.get(
            f"{INFOJOBS_API}/{offer_id}",
            headers=self._auth_headers(),
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        min_pay = data.get("minPay") or {}
        max_pay = data.get("maxPay") or {}
        salary_text = clean_text(data.get("salaryDescription"))
        if not salary_text and (min_pay or max_pay):
            salary_text = " - ".join(
                filter(None, [self._pay_value(min_pay), self._pay_value(max_pay)])
            ) or None
        city_pd = data.get("cityPD") or {}
        province = data.get("province") or {}
        profile = data.get("profile") or {}
        return JobRecord(
            source=self.source,
            external_id=str(data.get("id")),
            title=clean_text(data.get("title")) or "Oferta InfoJobs",
            company=clean_text(profile.get("name")),
            description=clean_text(data.get("description")),
            salary_text=salary_text,
            salary_min=self._pay_value(min_pay),
            salary_max=self._pay_value(max_pay),
            salary_currency="EUR" if salary_text else None,
            salary_period=clean_text(min_pay.get("periodValue") or max_pay.get("periodValue")),
            publication_date=parse_date(data.get("creationDate")),
            update_date=parse_date(data.get("updatedAt") or data.get("updateDate")),
            province=clean_text(province.get("value")),
            municipality=clean_text(city_pd.get("value") or data.get("city")),
            island=None,
            raw_location=clean_text(" / ".join(filter(None, [data.get("city"), province.get("value")]))),
            contract_type=clean_text((data.get("contractType") or {}).get("value")),
            workday=clean_text((data.get("journey") or {}).get("value")),
            schedule=None,
            vacancies=None,
            source_url=data.get("link") or f"https://www.infojobs.net/oferta/{offer_id}",
            scraped_at=JobRecord.now(),
        )

    @staticmethod
    def _pay_value(value: dict) -> str | None:
        if not value:
            return None
        raw = value.get("value")
        return clean_text(str(raw)) if raw is not None else None
