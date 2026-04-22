from __future__ import annotations

import re
from urllib.parse import urljoin

import requests
import urllib3
from bs4 import BeautifulSoup

from ..models import DegreeCatalogRecord
from ..report_extract import fetch_and_extract_report_description
from .base import DegreeSourceResult

ANECA_BASE_URL = "https://srv.aneca.es"
ANECA_GRADO_SEARCH_URL = (
    "https://srv.aneca.es/ListadoTitulos/search/site/"
    "?f%5B0%5D=im_field_titulo_ciclos%3A2000000001"
)


def parse_aneca_records(payload: list[dict]) -> DegreeSourceResult:
    records = [
        DegreeCatalogRecord(
            source="aneca",
            source_id=str(item.get("id") or item.get("codigo") or item.get("title")),
            university=item.get("university") or item.get("universidad") or "Unknown",
            title=item.get("title") or item.get("titulo") or "Unknown title",
            branch=item.get("branch") or item.get("rama"),
            center=item.get("center") or item.get("centro"),
            modality=item.get("modality") or item.get("modalidad"),
            language=item.get("language") or item.get("idioma"),
            credits=str(item.get("credits")) if item.get("credits") is not None else None,
            status=item.get("status") or item.get("estado"),
            memory_url=item.get("memory_url") or item.get("memoria"),
            report_url=item.get("report_url") or item.get("informe"),
            source_url=item.get("source_url") or item.get("url"),
            description=item.get("description"),
            description_source=item.get("description_source"),
            scraped_at=DegreeCatalogRecord.now(),
        )
        for item in payload
    ]
    return DegreeSourceResult(source="aneca", records=records)


def parse_aneca_search_page(html: str) -> list[dict[str, str | None]]:
    soup = BeautifulSoup(html, "html.parser")
    results: list[dict[str, str | None]] = []
    for item in soup.select("ol.search-results li.search-result"):
        title_node = item.select_one("h3.title")
        university_node = item.select_one("ul.search-snippet li")
        link_node = item.select_one("#imagen-lupa a[href]")
        if not title_node or not university_node or not link_node:
            continue
        results.append(
            {
                "title": title_node.get_text(" ", strip=True),
                "university": university_node.get_text(" ", strip=True),
                "branch": _dd_after_dt(item, "Rama"),
                "language": _dd_after_dt(item, "Idioma"),
                "source_url": urljoin(ANECA_BASE_URL, link_node.get("href")),
            }
        )
    return results


def parse_aneca_detail_page(html: str, source_url: str) -> dict[str, str | None]:
    soup = BeautifulSoup(html, "html.parser")
    headings = soup.select("h2")
    table = soup.select_one("table")
    report_url = None
    report_type = None
    report_year = None
    if table:
        rows = table.select("tr")
        detail_row = rows[1] if len(rows) > 1 else None
        if detail_row:
            cells = detail_row.select("td")
            if len(cells) >= 3:
                report_type = cells[0].get_text(" ", strip=True) or None
                report_year = cells[2].get_text(" ", strip=True) or None
            anchor = detail_row.select_one("a[href]")
            if anchor:
                report_url = urljoin(ANECA_BASE_URL, anchor.get("href"))
    return {
        "university": headings[0].get_text(" ", strip=True) if len(headings) > 0 else None,
        "center": headings[1].get_text(" ", strip=True) if len(headings) > 1 else None,
        "branch": headings[2].get_text(" ", strip=True) if len(headings) > 2 else None,
        "credits": _first_dd_after_label(soup, "Créditos ECTS"),
        "language": _first_dd_after_label(soup, "Idioma de impartición"),
        "report_url": report_url,
        "status": report_type,
        "report_year": report_year,
        "source_url": source_url,
    }


def fetch_aneca_degree_catalog(
    *,
    limit: int | None = None,
    max_pages: int | None = None,
    with_report_text: bool = False,
    verify_ssl: bool = False,
    timeout: int = 30,
) -> DegreeSourceResult:
    session = requests.Session()
    if not verify_ssl:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    records: list[DegreeCatalogRecord] = []
    page_index = 0

    while True:
        if max_pages is not None and page_index >= max_pages:
            break
        page_url = ANECA_GRADO_SEARCH_URL if page_index == 0 else f"{ANECA_GRADO_SEARCH_URL}&page={page_index}"
        response = session.get(page_url, timeout=timeout, verify=verify_ssl)
        response.raise_for_status()
        search_rows = parse_aneca_search_page(response.text)
        if not search_rows:
            break

        for row in search_rows:
            detail_response = session.get(row["source_url"], timeout=timeout, verify=verify_ssl)
            detail_response.raise_for_status()
            detail = parse_aneca_detail_page(detail_response.text, row["source_url"] or "")
            description = None
            description_source = None
            if with_report_text and detail.get("report_url"):
                description = fetch_and_extract_report_description(
                    detail["report_url"],
                    timeout=timeout,
                    verify_ssl=verify_ssl,
                )
                description_source = "aneca_report_pdf" if description else None
            source_id_match = re.search(r"/node/(\d+)", row["source_url"] or "")
            records.append(
                DegreeCatalogRecord(
                    source="aneca_live",
                    source_id=source_id_match.group(1) if source_id_match else row["title"] or "",
                    university=detail.get("university") or row["university"] or "Unknown",
                    title=row["title"] or "Unknown title",
                    branch=detail.get("branch") or row["branch"],
                    center=detail.get("center"),
                    language=detail.get("language") or row["language"],
                    credits=detail.get("credits"),
                    status=detail.get("status"),
                    report_url=detail.get("report_url"),
                    source_url=row["source_url"],
                    description=description,
                    description_source=description_source,
                    scraped_at=DegreeCatalogRecord.now(),
                )
            )
            if limit is not None and len(records) >= limit:
                return DegreeSourceResult(source="aneca_live", records=records[:limit])
        page_index += 1

    return DegreeSourceResult(source="aneca_live", records=records[:limit] if limit else records)


def _dd_after_dt(item, label: str) -> str | None:
    for dt in item.select("dt"):
        if label.lower() in dt.get_text(" ", strip=True).lower():
            sibling = dt.find_next("dd")
            if sibling:
                return sibling.get_text(" ", strip=True) or None
    return None


def _first_dd_after_label(soup: BeautifulSoup, label: str) -> str | None:
    for dt in soup.select("dt"):
        if label.lower() in dt.get_text(" ", strip=True).lower():
            sibling = dt.find_next("dd")
            if sibling:
                return sibling.get_text(" ", strip=True) or None
    return None
