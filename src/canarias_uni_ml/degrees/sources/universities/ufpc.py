from __future__ import annotations

from .base import UniversitySiteMemoryResolver


class UFPCMemoryResolver(UniversitySiteMemoryResolver):
    def __init__(self) -> None:
        super().__init__(
            university_id="ufpc",
            seed_url="https://www.fernandopessoa.com/es/",
            search_paths=(
                "/es/",
                "/es/grados/",
                "/es/masters/",
                "/es/doctorados/",
                "/es/calidad/",
                "/sitemap.xml",
            ),
            link_markers=("memoria", "verificacion", "verifica"),
        )
