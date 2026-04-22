from __future__ import annotations

import re
import unicodedata
from urllib.parse import urljoin

import requests
import urllib3
from bs4 import BeautifulSoup

from ..memory_resolver import resolve_missing_memory
from ..models import DegreeCatalogRecord
from ..report_extract import fetch_and_extract_report_description
from ..university_registry import match_canary_university
from .base import DegreeSourceResult

ANECA_BASE_URL = "https://srv.aneca.es"
ANECA_CATALOG_URL = "https://srv.aneca.es/ListadoTitulos/busqueda-titulaciones"
ANECA_SEARCH_URL_TEMPLATE = "https://srv.aneca.es/ListadoTitulos/search/site/?f%5B0%5D=im_field_titulo_ciclos%3A{cycle_id}"

TITLE_CYCLE_CONFIG = {
    "grado": {"id": "2000000001"},
    "master": {"id": "2000000002"},
    "doctorado": {"id": "2000000003"},
}
DEFAULT_TITLE_CYCLES = ("grado", "master", "doctorado")


def parse_aneca_records(payload: list[dict]) -> DegreeSourceResult:
    records = [
        DegreeCatalogRecord(
            source="aneca",
            source_id=str(item.get("id") or item.get("codigo") or item.get("title")),
            university=item.get("university") or item.get("universidad") or "Unknown",
            title=item.get("title") or item.get("titulo") or "Unknown title",
            title_type=item.get("title_type") or item.get("tipo_titulo"),
            university_id=item.get("university_id"),
            university_type=item.get("university_type"),
            branch=item.get("branch") or item.get("rama"),
            center=item.get("center") or item.get("centro"),
            modality=item.get("modality") or item.get("modalidad"),
            language=item.get("language") or item.get("idioma"),
            credits=str(item.get("credits")) if item.get("credits") is not None else None,
            status=item.get("status") or item.get("estado"),
            memory_url=item.get("memory_url") or item.get("memoria"),
            report_url=item.get("report_url") or item.get("informe"),
            source_url=item.get("source_url") or item.get("url"),
            memory_resolution_source=item.get("memory_resolution_source"),
            memory_resolution_status=item.get("memory_resolution_status"),
            memory_resolution_error=item.get("memory_resolution_error"),
            description=item.get("description"),
            description_source=item.get("description_source"),
            scraped_at=DegreeCatalogRecord.now(),
        )
        for item in payload
    ]
    return DegreeSourceResult(source="aneca", records=records)


def parse_aneca_search_page(html: str, title_type: str | None = None) -> list[dict[str, str | None]]:
    soup = BeautifulSoup(html, "html.parser")
    results: list[dict[str, str | None]] = []
    # Current ANECA listing uses a large views table at /busqueda-titulaciones.
    for item in soup.select("table.views-table tbody tr"):
        link_node = item.select_one("td.views-field-title a[href]")
        university_node = item.select_one("td.views-field-title-1, td.views-field-field-titulo-universidades")
        if not link_node:
            continue
        title = _normalize_degree_title(link_node.get_text(" ", strip=True))
        university = _normalize_space(university_node.get_text(" ", strip=True)) if university_node else None
        results.append(
            {
                "title": title,
                "title_type": title_type or _infer_title_type(title),
                "university": university,
                "source_url": urljoin(ANECA_BASE_URL, link_node.get("href")),
            }
        )
    if results:
        return results

    # Legacy fallback for historical HTML layout.
    for item in soup.select("ol.search-results li.search-result"):
        title_node = item.select_one("h3.title")
        university_node = item.select_one("ul.search-snippet li")
        link_node = item.select_one("#imagen-lupa a[href]")
        if not title_node or not university_node or not link_node:
            continue
        title = _normalize_degree_title(title_node.get_text(" ", strip=True))
        results.append(
            {
                "title": title,
                "title_type": title_type or _infer_title_type(title),
                "university": _normalize_space(university_node.get_text(" ", strip=True)),
                "branch": _dd_after_dt(item, "Rama"),
                "language": _dd_after_dt(item, "Idioma"),
                "source_url": urljoin(ANECA_BASE_URL, link_node.get("href")),
            }
        )
    return results


def parse_aneca_detail_page(html: str, source_url: str) -> dict[str, str | None]:
    soup = BeautifulSoup(html, "html.parser")
    headings = [_normalize_space(h.get_text(" ", strip=True)) for h in soup.select("h2") if h.get_text(" ", strip=True)]

    report_entries: list[dict[str, str | None]] = []
    for row in soup.select("table tr")[1:]:
        cells = row.select("td")
        if not cells:
            continue
        anchor = row.select_one("a[href]")
        if not anchor:
            continue
        raw_href = (anchor.get("href") or "").strip()
        if ".pdf" not in raw_href.lower():
            continue
        report_entries.append(
            {
                "url": urljoin(ANECA_BASE_URL, raw_href),
                "type": cells[0].get_text(" ", strip=True) if len(cells) >= 1 else None,
                "year": cells[2].get_text(" ", strip=True) if len(cells) >= 3 else None,
            }
        )
    if not report_entries:
        for anchor in soup.select("a[href]"):
            raw_href = (anchor.get("href") or "").strip()
            if ".pdf" not in raw_href.lower():
                continue
            report_entries.append({"url": urljoin(ANECA_BASE_URL, raw_href), "type": None, "year": None})

    chosen_report = _select_preferred_report(report_entries)
    report_urls = []
    seen_urls: set[str] = set()
    for entry in report_entries:
        url = entry.get("url")
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        report_urls.append(url)

    memory_urls = _extract_memory_urls(soup)

    center = None
    branch = None
    if len(headings) >= 3:
        center = headings[1]
        branch = headings[2]
    elif len(headings) == 2:
        branch = headings[1]
    if not branch:
        branch = _first_dd_after_label(soup, "Rama de conocimiento")
    return {
        "university": headings[0] if headings else None,
        "center": center,
        "branch": branch,
        "credits": _first_dd_after_label(soup, "Créditos ECTS"),
        "language": _first_dd_after_label(soup, "Idioma de impartición"),
        "report_url": chosen_report.get("url"),
        "status": chosen_report.get("type"),
        "report_year": chosen_report.get("year"),
        "report_urls": "|".join(report_urls) if report_urls else None,
        "memory_url": "|".join(memory_urls) if memory_urls else None,
        "source_url": source_url,
    }


def fetch_aneca_degree_catalog(
    *,
    cycles: tuple[str, ...] = DEFAULT_TITLE_CYCLES,
    limit: int | None = None,
    max_pages: int | None = None,
    with_report_text: bool = False,
    canary_only: bool = False,
    resolve_university_memory: bool = False,
    verify_ssl: bool = False,
    timeout: int = 30,
) -> DegreeSourceResult:
    session = requests.Session()
    if not verify_ssl:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    records: list[DegreeCatalogRecord] = []
    search_rows = _fetch_search_rows(
        session=session,
        timeout=timeout,
        verify_ssl=verify_ssl,
        max_pages=max_pages,
        cycles=cycles,
    )
    for row in search_rows:
        university_hint = row.get("university")
        matched_hint = match_canary_university(university_hint)
        if canary_only and not matched_hint:
            continue
        detail_response = session.get(row["source_url"], timeout=timeout, verify=verify_ssl)
        detail_response.raise_for_status()
        detail = parse_aneca_detail_page(detail_response.text, row["source_url"] or "")
        university = detail.get("university") or university_hint
        matched = match_canary_university(university) or matched_hint
        if canary_only and not matched:
            continue

        source_id_match = re.search(r"/node/(\d+)", row["source_url"] or "")
        record = DegreeCatalogRecord(
            source="aneca_live",
            source_id=source_id_match.group(1) if source_id_match else row["title"] or "",
            university=matched.canonical_name if matched else (university or "Unknown"),
            title=row["title"] or "Unknown title",
            title_type=row.get("title_type"),
            university_id=matched.university_id if matched else None,
            university_type=matched.university_type if matched else None,
            branch=detail.get("branch") or row.get("branch"),
            center=detail.get("center"),
            language=detail.get("language") or row.get("language"),
            credits=detail.get("credits"),
            status=detail.get("status"),
            memory_url=detail.get("memory_url") or detail.get("report_urls"),
            report_url=detail.get("report_url"),
            source_url=row["source_url"],
            memory_resolution_source="aneca_detail" if detail.get("memory_url") or detail.get("report_urls") else None,
            memory_resolution_status="resolved" if detail.get("memory_url") or detail.get("report_urls") else "unresolved",
            scraped_at=DegreeCatalogRecord.now(),
        )

        if resolve_university_memory and not record.memory_url:
            resolved = resolve_missing_memory(record)
            record.memory_url = resolved.memory_url
            record.memory_resolution_source = resolved.source
            record.memory_resolution_status = resolved.status
            record.memory_resolution_error = resolved.error

        description = None
        description_source = None
        if with_report_text:
            candidate_urls = _candidate_report_urls(record)
            for candidate_url in candidate_urls:
                description = fetch_and_extract_report_description(
                    candidate_url,
                    timeout=timeout,
                    verify_ssl=verify_ssl,
                )
                if description:
                    description_source = "aneca_report_pdf"
                    break
        record.description = description
        record.description_source = description_source
        records.append(record)

        if limit is not None and len(records) >= limit:
            return DegreeSourceResult(source="aneca_live", records=records[:limit])

    return DegreeSourceResult(source="aneca_live", records=records[:limit] if limit else records)


def _fetch_search_rows(
    *,
    session: requests.Session,
    timeout: int,
    verify_ssl: bool,
    max_pages: int | None,
    cycles: tuple[str, ...],
) -> list[dict[str, str | None]]:
    records: list[dict[str, str | None]] = []
    for cycle in cycles:
        cycle_key = (cycle or "").strip().lower()
        if cycle_key not in TITLE_CYCLE_CONFIG:
            raise ValueError(f"Unsupported cycle: {cycle}")
        cycle_id = TITLE_CYCLE_CONFIG[cycle_key]["id"]
        response = session.get(
            ANECA_CATALOG_URL,
            params={"field_titulo_ciclos_tid": cycle_id},
            timeout=timeout,
            verify=verify_ssl,
        )
        response.raise_for_status()
        rows = parse_aneca_search_page(response.text, title_type=cycle_key)
        if rows:
            records.extend(rows)
            continue

        page_index = 0
        while True:
            if max_pages is not None and page_index >= max_pages:
                break
            page_url = ANECA_SEARCH_URL_TEMPLATE.format(cycle_id=cycle_id)
            if page_index > 0:
                page_url = f"{page_url}&page={page_index}"
            page_response = session.get(page_url, timeout=timeout, verify=verify_ssl)
            page_response.raise_for_status()
            page_rows = parse_aneca_search_page(page_response.text, title_type=cycle_key)
            if not page_rows:
                break
            records.extend(page_rows)
            page_index += 1
    return records


def _candidate_report_urls(record: DegreeCatalogRecord) -> list[str]:
    urls: list[str] = []
    if record.report_url:
        urls.append(record.report_url)
    if record.memory_url:
        urls.extend(url for url in record.memory_url.split("|") if url and url not in urls)
    return urls


def _extract_memory_urls(soup: BeautifulSoup) -> list[str]:
    urls: list[str] = []
    for anchor in soup.select("a[href]"):
        href = (anchor.get("href") or "").strip()
        if ".pdf" not in href.lower():
            continue
        label = anchor.get_text(" ", strip=True).lower()
        if "memoria" not in label and "memoria" not in href.lower():
            continue
        resolved = urljoin(ANECA_BASE_URL, href)
        if resolved not in urls:
            urls.append(resolved)
    return urls


def _normalize_space(text: str) -> str:
    return " ".join(text.split())


def _normalize_degree_title(title: str) -> str:
    clean = _normalize_space(title)
    clean = re.sub(r"(?i)^grado en\s+grado en\s+", "Grado en ", clean)
    clean = re.sub(r"(?i)^master en\s+master en\s+", "Master en ", clean)
    clean = re.sub(r"(?i)^doctorado en\s+doctorado en\s+", "Doctorado en ", clean)
    return clean


def _normalize_for_match(text: str | None) -> str:
    if not text:
        return ""
    normalized = unicodedata.normalize("NFD", text)
    no_accents = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    return _normalize_space(no_accents).lower()


def _infer_title_type(title: str | None) -> str | None:
    normalized = _normalize_for_match(title)
    if normalized.startswith("grado"):
        return "grado"
    if normalized.startswith("master"):
        return "master"
    if normalized.startswith("doctorado"):
        return "doctorado"
    return None


def _report_year_as_int(raw_year: str | None) -> int:
    if not raw_year:
        return -1
    match = re.search(r"(19|20)\d{2}", raw_year)
    if not match:
        return -1
    return int(match.group(0))


def _select_preferred_report(report_entries: list[dict[str, str | None]]) -> dict[str, str | None]:
    if not report_entries:
        return {"url": None, "type": None, "year": None}
    return max(report_entries, key=lambda item: (_report_year_as_int(item.get("year")), item.get("url") or ""))


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
