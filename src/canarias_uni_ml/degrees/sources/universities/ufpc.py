from __future__ import annotations

import requests

from .base import MemoryResolution, StaticHtmlMemoryResolver


class UFPCMemoryResolver(StaticHtmlMemoryResolver):
    def __init__(self) -> None:
        super().__init__(
            university_id="ufpc",
            seed_url="https://www.fernandopessoa.com/es/",
            link_markers=("memoria", "verificacion", "verifica"),
        )

    def resolve(self, title: str) -> MemoryResolution:
        try:
            response = requests.get(self.seed_url, timeout=20)
            response.raise_for_status()
            return self.resolve_from_html(response.text)
        except Exception as exc:  # pragma: no cover - network variance
            return MemoryResolution(None, "university_ufpc", "unresolved", f"network_error:{type(exc).__name__}")
