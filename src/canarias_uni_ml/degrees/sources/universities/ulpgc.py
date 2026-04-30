from __future__ import annotations

from .base import UniversitySiteMemoryResolver


class ULPGCMemoryResolver(UniversitySiteMemoryResolver):
    def __init__(self) -> None:
        super().__init__(
            university_id="ulpgc",
            seed_url="https://www.ulpgc.es/",
            search_paths=(
                "/",
                "/estudios/",
                "/masteres",
                "/doctorados",
                "/calidad",
                "/sitemap.xml",
            ),
            link_markers=("memoria", "verificacion", "verifica"),
        )
