from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urljoin

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


class StaticHtmlMemoryResolver:
    university_id: str
    seed_url: str

    def __init__(self, *, university_id: str, seed_url: str, link_markers: tuple[str, ...] = ("memoria", "verificacion")):
        self.university_id = university_id
        self.seed_url = seed_url
        self._link_markers = tuple(marker.lower() for marker in link_markers)

    def resolve_from_html(self, html: str) -> MemoryResolution:
        soup = BeautifulSoup(html, "html.parser")
        for anchor in soup.select("a[href]"):
            href = (anchor.get("href") or "").strip()
            if not href:
                continue
            if ".pdf" not in href.lower():
                continue
            label = anchor.get_text(" ", strip=True).lower()
            if any(marker in label or marker in href.lower() for marker in self._link_markers):
                return MemoryResolution(
                    memory_url=urljoin(self.seed_url, href),
                    source=f"university_{self.university_id}",
                    status="resolved",
                )
        return MemoryResolution(
            memory_url=None,
            source=f"university_{self.university_id}",
            status="unresolved",
            error="no_memory_link_found",
        )
