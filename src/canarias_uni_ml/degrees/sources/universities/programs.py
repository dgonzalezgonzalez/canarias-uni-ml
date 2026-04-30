from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from bs4.element import Tag

from ...program_validation import infer_title_type, is_valid_program_candidate


@dataclass(frozen=True, slots=True)
class ProgramCandidate:
    title: str
    title_type: str
    source_url: str
    evidence_urls: tuple[str, ...] = ()


def parse_anchor_programs(html: str, *, page_url: str, default_title_type: str | None = None) -> list[ProgramCandidate]:
    soup = BeautifulSoup(html, "html.parser")
    candidates: list[ProgramCandidate] = []
    for anchor in soup.select("a[href]"):
        href = (anchor.get("href") or "").strip()
        if not href or href.startswith("#"):
            continue
        absolute = urljoin(page_url, href)
        label = normalize_program_title(anchor.get_text(" ", strip=True))
        title_type = default_title_type or infer_title_type(f"{label} {absolute}")
        if not title_type or not is_valid_program_candidate(label, absolute, title_type):
            continue
        candidates.append(ProgramCandidate(title=label, title_type=title_type, source_url=absolute))
    return dedupe_candidates(candidates)


def parse_heading_programs(
    html: str,
    *,
    page_url: str,
    default_title_type: str | None = None,
) -> list[ProgramCandidate]:
    soup = BeautifulSoup(html, "html.parser")
    candidates: list[ProgramCandidate] = []
    for heading in soup.find_all(["h2", "h3", "h4"]):
        if not isinstance(heading, Tag):
            continue
        title = normalize_program_title(heading.get_text(" ", strip=True))
        title_type = default_title_type or infer_title_type(title)
        if not title_type or not is_valid_program_candidate(title, page_url, title_type):
            continue
        source_url, evidence_urls = _links_near_heading(heading, page_url)
        candidates.append(
            ProgramCandidate(
                title=title,
                title_type=title_type,
                source_url=source_url or page_url,
                evidence_urls=evidence_urls,
            )
        )
    return dedupe_candidates(candidates)


def dedupe_candidates(candidates: list[ProgramCandidate]) -> list[ProgramCandidate]:
    deduped: dict[tuple[str, str], ProgramCandidate] = {}
    for candidate in candidates:
        key = (candidate.title.lower(), candidate.title_type)
        existing = deduped.get(key)
        if existing is None or _candidate_rank(candidate) > _candidate_rank(existing):
            deduped[key] = candidate
    return list(deduped.values())


def normalize_program_title(value: str) -> str:
    text = " ".join((value or "").split()).strip()
    text = text.replace("Nuevo/New", "").strip()
    for suffix in ("Nuevo en 2026/2027", "Nuevo en 2026", "Plan nuevo (2026)", "Plan nuevo", "Nuevo"):
        if text.endswith(suffix):
            text = text[: -len(suffix)].strip()
    if text.lower().startswith("doble titulación:"):
        remainder = text.split(":", 1)[1].strip()
        if remainder.lower().startswith("grado en "):
            remainder = remainder[9:].strip()
        text = "Doble Grado en " + remainder
    return text[:250] if text else "Unknown title"


def _links_near_heading(heading: Tag, page_url: str) -> tuple[str | None, tuple[str, ...]]:
    links: list[tuple[str, str]] = []
    containers = [heading.parent]
    if heading.parent and heading.parent.parent:
        containers.append(heading.parent.parent)
    for container in containers:
        if not isinstance(container, Tag):
            continue
        for anchor in container.select("a[href]"):
            text = " ".join(anchor.get_text(" ", strip=True).split()).lower()
            href = (anchor.get("href") or "").strip()
            if not href or href.startswith("#"):
                continue
            links.append((text, urljoin(page_url, href)))
    for sibling in heading.find_next_siblings(limit=8):
        if isinstance(sibling, Tag) and sibling.name in {"h1", "h2", "h3", "h4"}:
            break
        if not isinstance(sibling, Tag):
            continue
        for anchor in sibling.select("a[href]"):
            text = " ".join(anchor.get_text(" ", strip=True).split()).lower()
            href = (anchor.get("href") or "").strip()
            if href and not href.startswith("#"):
                links.append((text, urljoin(page_url, href)))
    seen: dict[str, str] = {}
    for text, url in links:
        seen[url] = text
    for url, text in seen.items():
        if "web del t" in text or "web site" in text or "explora" in text or "más" in text or "mas" in text:
            return url, tuple(seen.keys())
    for url in seen:
        if not url.lower().endswith(".pdf") and not url.startswith("mailto:"):
            return url, tuple(seen.keys())
    return None, tuple(seen.keys())


def _candidate_rank(candidate: ProgramCandidate) -> int:
    url = candidate.source_url.lower()
    score = len(candidate.evidence_urls)
    if not url.endswith(".pdf"):
        score += 5
    if "www2.ulpgc.es" in url or "plan-estudio" in url:
        score += 3
    return score
