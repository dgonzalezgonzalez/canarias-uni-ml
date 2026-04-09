from __future__ import annotations

import base64
import os

import requests

from ..models import JobRecord
from ..utils import clean_text, parse_date
from .base import SpiderError, SpiderResult


INFOJOBS_API = "https://api.infojobs.net/api/9/offer"


class InfoJobsSpider:
    source = "infojobs"

    def __init__(self) -> None:
        self.client_id = os.getenv("INFOJOBS_CLIENT_ID")
        self.client_secret = os.getenv("INFOJOBS_CLIENT_SECRET")
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0", "Accept": "application/json"})

    def fetch(self, limit: int) -> SpiderResult:
        if not self.client_id or not self.client_secret:
            raise SpiderError("InfoJobs requires INFOJOBS_CLIENT_ID and INFOJOBS_CLIENT_SECRET")
        offers = self._fetch_list(limit)
        records = [self._fetch_detail(offer["id"]) for offer in offers[:limit]]
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
