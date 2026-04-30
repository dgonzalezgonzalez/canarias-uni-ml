from __future__ import annotations

import hashlib
import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from ..program_validation import infer_title_type, is_valid_program_candidate
from ..models import DegreeCatalogRecord
from ..program_page_resolver import (
    UNIVERSITY_BASE,
    UNIVERSITY_SEARCH_PATHS,
    extract_program_description_from_html,
)
from ..university_registry import load_canary_university_registry
from .base import DegreeSourceResult
from .universities.programs import ProgramCandidate, dedupe_candidates, normalize_program_title, parse_anchor_programs
from .universities.uec_programs import parse_uec_programs
from .universities.ufpc_programs import parse_ufpc_programs
from .universities.uhesp_programs import parse_uhesp_programs
from .universities.ull_programs import parse_ull_programs
from .universities.ulpgc_programs import parse_ulpgc_programs
from .universities.uam_programs import parse_uam_programs

PROGRAM_PARSERS = {
    "ull": parse_ull_programs,
    "ulpgc": parse_ulpgc_programs,
    "uec": parse_uec_programs,
    "uam": parse_uam_programs,
    "ufpc": parse_ufpc_programs,
    "uhesp": parse_uhesp_programs,
}


def fetch_university_official_catalog(
    *,
    cycles: tuple[str, ...] = ("grado", "master", "doctorado"),
    limit: int | None = None,
    timeout: int = 15,
    fetch_descriptions: bool = True,
    max_candidates_per_index: int = 120,
) -> DegreeSourceResult:
    allowed_cycles = {item.strip().lower() for item in cycles if item.strip()}
    records: list[DegreeCatalogRecord] = []
    seen_keys: set[tuple[str, str, str]] = set()

    for university in load_canary_university_registry():
        university_id = university.university_id
        base = UNIVERSITY_BASE.get(university_id)
        search_paths = UNIVERSITY_SEARCH_PATHS.get(university_id, ())
        if not base or not search_paths:
            continue

        session = requests.Session()
        session.headers.update({"User-Agent": "Mozilla/5.0"})
        for path in search_paths:
            page_url = urljoin(base, path)
            try:
                response = session.get(page_url, timeout=timeout)
                response.raise_for_status()
            except requests.RequestException:
                continue

            candidates = extract_program_candidates_from_index(
                response.text,
                page_url=page_url,
                university_id=university_id,
                default_title_type=_title_type_from_path(path),
            )
            for candidate in candidates[:max_candidates_per_index]:
                source_url = candidate.source_url
                title_type = candidate.title_type
                title = candidate.title
                key = (university_id, title.lower(), title_type)
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                if title_type not in allowed_cycles:
                    continue

                description = None
                status = "missing"
                quality = None
                if fetch_descriptions:
                    try:
                        detail = session.get(source_url, timeout=timeout)
                        detail.raise_for_status()
                        description = extract_program_description_from_html(detail.text)
                        if description:
                            status = "ok"
                            quality = "high" if len(description) >= 500 else "medium"
                    except requests.RequestException:
                        status = "error"

                records.append(
                    DegreeCatalogRecord(
                        source="university_official_live",
                        source_id=_stable_source_id(university_id, title, source_url),
                        university=university.canonical_name,
                        title=title,
                        title_type=title_type,
                        university_id=university_id,
                        university_type=university.university_type,
                        source_url=source_url,
                        description=description,
                        description_source_type="university_program_page" if description else None,
                        description_source_url=source_url if description else None,
                        description_status=status,
                        description_quality_flag=quality,
                        description_source="university_program_page" if description else None,
                        scraped_at=DegreeCatalogRecord.now(),
                    )
                )
                if limit is not None and len(records) >= limit:
                    return DegreeSourceResult(source="university_official_live", records=records)
    return DegreeSourceResult(source="university_official_live", records=records)


def extract_program_links_from_index(html: str, *, page_url: str) -> list[dict[str, str | None]]:
    return [
        {
            "title": candidate.title,
            "title_type": candidate.title_type,
            "source_url": candidate.source_url,
        }
        for candidate in extract_program_candidates_from_index(html, page_url=page_url)
    ]


def extract_program_candidates_from_index(
    html: str,
    *,
    page_url: str,
    university_id: str | None = None,
    default_title_type: str | None = None,
) -> list[ProgramCandidate]:
    parser = PROGRAM_PARSERS.get(university_id or "")
    if parser:
        candidates = parser(html, page_url=page_url, title_type=default_title_type)
    else:
        candidates = parse_anchor_programs(html, page_url=page_url, default_title_type=default_title_type)
    return dedupe_candidates(
        [
            candidate
            for candidate in candidates
            if is_valid_program_candidate(candidate.title, candidate.source_url, candidate.title_type)
        ]
    )


def _looks_like_program_url(url: str) -> bool:
    parsed = urlparse(url)
    path = parsed.path.lower()
    if not path:
        return False
    has_degree_marker = any(marker in path for marker in ("grado", "grados", "master", "masters", "máster", "doctorado"))
    if not has_degree_marker and "estudios" not in path:
        return False
    noisy = ("blog", "noticia", "news", "event", "contact", "legal", "privacy", "sitemap")
    return not any(marker in path for marker in noisy)


def _stable_source_id(university_id: str, title: str, source_url: str) -> str:
    digest = hashlib.sha1(f"{title}|{source_url}".encode("utf-8")).hexdigest()[:12]
    return f"{university_id}_{digest}"


def _normalize_match(text: str | None) -> str:
    return " ".join((text or "").lower().split())


def _title_from_url(url: str) -> str:
    parsed = urlparse(url)
    slug = parsed.path.rstrip("/").split("/")[-1].replace("-", " ").strip()
    if not slug:
        return "Unknown title"
    return slug.title()


def _title_type_from_path(path: str) -> str | None:
    value = _normalize_match(path)
    if "doctor" in value:
        return "doctorado"
    if "master" in value or "máster" in value:
        return "master"
    if "grado" in value:
        return "grado"
    return None
