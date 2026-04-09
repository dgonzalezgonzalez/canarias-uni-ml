from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from src.canarias_jobs.spiders.indeed_api import IndeedApiSpider, MOSAIC_PATTERN


SAMPLE_MOSAIC_DATA = {
    "metaData": {
        "mosaicProviderJobCardsModel": {
            "results": [
                {
                    "jobkey": "abc123",
                    "title": "Software Engineer",
                    "companyName": "Tech Corp",
                    "formattedLocation": "Las Palmas de Gran Canaria, ES",
                    "salary": "30.000 € - 45.000 €",
                    "date": "Thu, 09 Apr 2026 12:00:00 GMT",
                    "snippet": "Full stack developer position",
                },
                {
                    "jobkey": "def456",
                    "title": "Data Analyst",
                    "companyName": "Data Inc",
                    "formattedLocation": "Santa Cruz de Tenerife, ES",
                    "salary": "25.000 € - 35.000 € a year",
                    "date": "Wed, 08 Apr 2026 08:00:00 GMT",
                    "snippet": "Data analysis role",
                },
            ]
        }
    }
}


class TestMosaicPattern:
    def test_extracts_mosaic_data(self):
        html = """
        <html><body>
        <script>
        window.mosaic.providerData["mosaic-provider-jobcards"]={"metaData":{"test":true}};
        </script>
        </body></html>
        """
        match = MOSAIC_PATTERN.search(html)
        assert match is not None
        data = json.loads(match.group(1))
        assert data["metaData"]["test"] is True

    def test_handles_multiline_data(self):
        html = """
        <html><body>
        <script>
        window.mosaic.providerData["mosaic-provider-jobcards"]={
            "metaData": {
                "test": "value"
            }
        };
        </script>
        </body></html>
        """
        match = MOSAIC_PATTERN.search(html)
        assert match is not None


class TestIndeedApiSpider:
    def test_normalize_job(self):
        spider = IndeedApiSpider()
        job = {
            "jobkey": "test123",
            "title": "Python Developer",
            "companyName": "TestCo",
            "formattedLocation": "Madrid, ES",
            "salary": "40.000 €",
            "date": "Thu, 09 Apr 2026 12:00:00 GMT",
        }
        detail = {}
        record = spider._normalize_job(job, detail)
        assert record.source == "indeed"
        assert record.external_id == "test123"
        assert record.title == "Python Developer"
        assert record.company == "TestCo"
        assert record.municipality == "Madrid"
        assert record.salary_text == "40.000 €"
        assert record.publication_date == "2026-04-09"

    def test_normalize_job_with_detail(self):
        spider = IndeedApiSpider()
        job = {
            "jobkey": "test123",
            "title": "Python Developer",
            "companyName": "TestCo",
            "formattedLocation": "Madrid, ES",
            "date": "Thu, 09 Apr 2026 12:00:00 GMT",
        }
        detail = {
            "description": "Full job description here",
            "salary_text": "35.000 €",
            "contract_type": "Indefinido",
        }
        record = spider._normalize_job(job, detail)
        assert record.description == "Full job description here"
        assert record.salary_text == "35.000 €"
        assert record.contract_type == "Indefinido"

    def test_normalize_job_no_location(self):
        spider = IndeedApiSpider()
        job = {
            "jobkey": "test456",
            "title": "DevOps Engineer",
            "formattedLocation": "",
        }
        detail = {}
        record = spider._normalize_job(job, detail)
        assert record.municipality is None
        assert record.province == "Las Palmas"

    def test_normalize_job_full_location(self):
        spider = IndeedApiSpider()
        job = {
            "jobkey": "test789",
            "title": "Designer",
            "companyName": "ArtCo",
            "formattedLocation": "Las Palmas de Gran Canaria, Las Palmas",
        }
        detail = {}
        record = spider._normalize_job(job, detail)
        assert record.municipality == "Las Palmas de Gran Canaria"
        assert record.province == "Las Palmas"

    def test_parse_date_valid(self):
        spider = IndeedApiSpider()
        result = spider._parse_date("Thu, 09 Apr 2026 12:00:00 GMT")
        assert result == "2026-04-09"

    def test_parse_date_invalid(self):
        spider = IndeedApiSpider()
        result = spider._parse_date("invalid")
        assert result is None

    def test_parse_date_empty(self):
        spider = IndeedApiSpider()
        result = spider._parse_date("")
        assert result is None

    def test_extract_jobs_valid(self):
        spider = IndeedApiSpider()
        data_json = json.dumps(SAMPLE_MOSAIC_DATA)
        html = f'<script>window.mosaic.providerData["mosaic-provider-jobcards"]={data_json};</script>\n'
        jobs = spider._extract_jobs(html)
        assert len(jobs) == 2
        assert jobs[0]["jobkey"] == "abc123"
        assert jobs[1]["jobkey"] == "def456"

    def test_extract_jobs_no_match(self):
        spider = IndeedApiSpider()
        html = "<html><body>No mosaic data here</body></html>"
        jobs = spider._extract_jobs(html)
        assert jobs == []

    def test_extract_detail_valid_html(self):
        spider = IndeedApiSpider()
        html = """
        <html><body>
        <div id="jobDescriptionText">
            We are looking for a Python Developer with experience in Django.
            Requirements:
            - Python 3.8+
            - Django framework
        </div>
        <span class="salary">35.000 € - 45.000 €</span>
        </body></html>
        """
        detail = spider._extract_detail(html)
        assert detail["description"] is not None
        assert "Python Developer" in detail["description"]
        assert detail["salary_text"] is not None
        assert "35.000" in detail["salary_text"]

    def test_extract_detail_no_description(self):
        spider = IndeedApiSpider()
        html = "<html><body><p>No job description here</p></body></html>"
        detail = spider._extract_detail(html)
        assert detail["description"] is None

    def test_scrapingbee_fallback(self):
        with patch.dict("os.environ", {"SCRAPINGBEE_API_KEY": "test-key"}):
            spider = IndeedApiSpider()
            assert spider.scrapingbee_key == "test-key"

    def test_scrapingbee_no_key(self):
        with patch.dict("os.environ", {}, clear=True):
            spider = IndeedApiSpider()
            assert spider.scrapingbee_key is None
