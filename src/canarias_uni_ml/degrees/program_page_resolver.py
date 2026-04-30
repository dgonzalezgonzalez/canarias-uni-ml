from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


@dataclass(slots=True)
class ProgramPageResolution:
    description: str | None
    source_url: str | None
    status: str
    quality_flag: str | None = None
    error: str | None = None


UNIVERSITY_SEARCH_PATHS = {
    "ull": ("/grados/", "/masteres/", "/doctorados/listado-doctorados/", "/"),
    "ulpgc": ("/grados", "/masteres", "/doctorado", "/"),
    "uec": ("/grados-canarias/", "/postgrados-canarias/", "/canarias/doctorados/", "/"),
    "uam": ("/planestudios?tipoestudio=gr", "/planestudios?tipoestudio=pg", "/", "/doctorados/"),
    "ufpc": ("/titulaciones-normativa/grado/", "/titulaciones-normativa/master/", "/", "/doctorado/"),
    "uhesp": ("/estudios/grados/", "/estudios/masteres/", "/estudios/doctorados/", "/estudios/"),
}

UNIVERSITY_BASE = {
    "ull": "https://www.ull.es",
    "ulpgc": "https://www.ulpgc.es",
    "uec": "https://universidadeuropea.com",
    "uam": "https://www.universidadatlanticomedio.es",
    "ufpc": "https://www.ufpcanarias.com",
    "uhesp": "https://hesperides.edu.es",
}


def resolve_program_page_description(university_id: str | None, title: str, *, timeout: int = 20) -> ProgramPageResolution:
    if not university_id or university_id not in UNIVERSITY_BASE:
        return ProgramPageResolution(None, None, "missing", error="no_program_page_resolver")

    base = UNIVERSITY_BASE[university_id]
    search_paths = UNIVERSITY_SEARCH_PATHS.get(university_id, ("/",))

    try:
        for path in search_paths:
            page_url = urljoin(base, path)
            response = requests.get(page_url, timeout=timeout)
            response.raise_for_status()
            candidate = _find_best_program_page(response.text, page_url, title=title)
            if not candidate:
                continue
            detail_response = requests.get(candidate, timeout=timeout)
            detail_response.raise_for_status()
            description = extract_program_description_from_html(detail_response.text)
            if description:
                quality_flag = "high" if len(description) >= 500 else "medium"
                return ProgramPageResolution(description, candidate, "ok", quality_flag=quality_flag)
    except requests.RequestException as exc:
        return ProgramPageResolution(None, None, "error", error=f"program_page_error:{type(exc).__name__}")

    return ProgramPageResolution(None, None, "missing", error="program_page_not_found")


def extract_program_description_from_html(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")

    # Prefer explicit description sections.
    for heading in soup.find_all(re.compile("h[1-4]")):
        heading_text = heading.get_text(" ", strip=True).lower()
        if not any(marker in heading_text for marker in ("descrip", "presentaci", "objetiv", "perfil")):
            continue
        blocks: list[str] = []
        for sibling in heading.find_all_next(["p", "li"], limit=8):
            text = " ".join(sibling.get_text(" ", strip=True).split())
            if len(text) >= 80:
                blocks.append(text)
            if len(" ".join(blocks)) >= 800:
                break
        if blocks:
            return " ".join(blocks)[:4000]

    # Fallback to long meaningful paragraphs on page.
    paragraphs = [
        " ".join(node.get_text(" ", strip=True).split())
        for node in soup.select("main p, article p, section p, .content p")
    ]
    long_paragraphs = [text for text in paragraphs if len(text) >= 120]
    if not long_paragraphs:
        return None
    return " ".join(long_paragraphs[:4])[:4000]


def _find_best_program_page(html: str, page_url: str, *, title: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    candidates: list[tuple[int, str]] = []
    title_tokens = _title_tokens(title)
    for anchor in soup.select("a[href]"):
        href = (anchor.get("href") or "").strip()
        if not href or href.startswith("#"):
            continue
        absolute = urljoin(page_url, href)
        label = anchor.get_text(" ", strip=True).lower()
        score = 0
        if any(x in absolute.lower() for x in ("grado", "master", "doctorado", "estudios")):
            score += 3
        if any(tok in label or tok in absolute.lower() for tok in title_tokens):
            score += 5
        if len(label) >= 20:
            score += 1
        if score > 0:
            candidates.append((score, absolute))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def _title_tokens(title: str) -> list[str]:
    clean = "".join(ch.lower() if ch.isalnum() else " " for ch in title)
    tokens = [tok for tok in clean.split() if len(tok) > 3]
    stop = {"grado", "master", "doctorado", "universitario", "oficial", "titulo"}
    return [tok for tok in tokens if tok not in stop]
