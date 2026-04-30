from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


@dataclass(slots=True)
class MemoryResolution:
    memory_url: str | None
    source: str
    status: str
    error: str | None = None


class UniversityMemoryResolver(Protocol):
    university_id: str

    def resolve(self, title: str) -> MemoryResolution:
        ...


@dataclass(frozen=True, slots=True)
class _PdfCandidate:
    url: str
    label: str
    page_url: str


class UniversitySiteMemoryResolver:
    university_id: str

    def __init__(
        self,
        *,
        university_id: str,
        seed_url: str,
        search_paths: tuple[str, ...],
        link_markers: tuple[str, ...] = ("memoria", "verificacion"),
    ):
        self.university_id = university_id
        self.seed_url = seed_url
        self._search_urls = tuple(urljoin(seed_url, path) for path in search_paths)
        self._link_markers = tuple(marker.lower() for marker in link_markers)

    def resolve(self, title: str) -> MemoryResolution:
        candidates: list[_PdfCandidate] = []
        errors: list[str] = []
        for page_url in self._search_urls:
            try:
                response = requests.get(page_url, timeout=20)
                response.raise_for_status()
                candidates.extend(self._extract_candidates(response.text, page_url))
            except Exception as exc:  # pragma: no cover - network variance
                errors.append(f"{page_url}:{type(exc).__name__}")
        return self._pick_candidate(candidates, title=title, errors=errors)

    def resolve_from_html(self, html: str, *, title: str = "", page_url: str | None = None) -> MemoryResolution:
        page = page_url or self.seed_url
        candidates = self._extract_candidates(html, page)
        return self._pick_candidate(candidates, title=title, errors=[])

    def _extract_candidates(self, html: str, page_url: str) -> list[_PdfCandidate]:
        candidates: list[_PdfCandidate] = []
        parser = "xml" if html.lstrip().startswith("<?xml") else "html.parser"
        soup = BeautifulSoup(html, parser)
        for anchor in soup.select("a[href]"):
            href = (anchor.get("href") or "").strip()
            if not href:
                continue
            if ".pdf" not in href.lower():
                continue
            label = anchor.get_text(" ", strip=True).lower()
            if any(marker in label or marker in href.lower() for marker in self._link_markers):
                candidates.append(
                    _PdfCandidate(
                        url=urljoin(page_url, href),
                        label=label,
                        page_url=page_url,
                    )
                )
        return candidates

    def _pick_candidate(self, candidates: list[_PdfCandidate], *, title: str, errors: list[str]) -> MemoryResolution:
        if not candidates:
            error = "no_memory_link_found"
            if errors:
                error = f"{error};" + ";".join(errors[:3])
            return MemoryResolution(
                memory_url=None,
                source=f"university_{self.university_id}",
                status="unresolved",
                error=error,
            )
        scored = sorted(candidates, key=lambda item: self._score(item, title), reverse=True)
        best = scored[0]
        return MemoryResolution(
            memory_url=best.url,
            source=f"university_{self.university_id}",
            status="resolved",
            error=None,
        )

    def _score(self, candidate: _PdfCandidate, title: str) -> int:
        haystack = f"{candidate.label} {candidate.url}".lower()
        score = 0
        if "memoria" in haystack:
            score += 10
        if "verifica" in haystack or "verificacion" in haystack:
            score += 6
        title_tokens = [tok for tok in _normalize_title_tokens(title) if len(tok) > 3]
        overlap = sum(1 for tok in title_tokens if tok in haystack)
        score += overlap * 3
        if candidate.url.lower().endswith(".pdf"):
            score += 1
        return score


def _normalize_title_tokens(title: str) -> list[str]:
    clean = "".join(ch.lower() if ch.isalnum() else " " for ch in title)
    tokens = [tok for tok in clean.split() if tok]
    drop = {"grado", "master", "doctorado", "universitario", "oficial", "titulo"}
    return [tok for tok in tokens if tok not in drop]


class StaticHtmlMemoryResolver(UniversitySiteMemoryResolver):
    def __init__(self, *, university_id: str, seed_url: str, link_markers: tuple[str, ...] = ("memoria", "verificacion")):
        super().__init__(
            university_id=university_id,
            seed_url=seed_url,
            search_paths=("/",),
            link_markers=link_markers,
        )

    def resolve(self, title: str) -> MemoryResolution:  # pragma: no cover - legacy behavior
        return super().resolve(title)

    def resolve_from_html(self, html: str) -> MemoryResolution:  # type: ignore[override]
        # Backward-compatible helper for tests calling legacy signature.
        return super().resolve_from_html(html, title="", page_url=self.seed_url)


def unresolved_resolution(university_id: str, reason: str) -> MemoryResolution:
    return MemoryResolution(
        memory_url=None,
        source=f"university_{university_id}",
        status="unresolved",
        error=reason,
    )
