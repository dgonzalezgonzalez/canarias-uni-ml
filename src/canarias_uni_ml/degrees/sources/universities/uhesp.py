from __future__ import annotations

from .base import UniversitySiteMemoryResolver


class UHESPMemoryResolver(UniversitySiteMemoryResolver):
    def __init__(self) -> None:
        super().__init__(
            university_id="uhesp",
            seed_url="https://hesperides.edu.es/",
            search_paths=(
                "/estudios/",
                "/estudios/grados/",
                "/estudios/masteres/",
                "/estudios/doctorados/",
                "/sitemap.xml",
            ),
            link_markers=("memoria", "verificacion", "verifica", "calidad"),
        )
