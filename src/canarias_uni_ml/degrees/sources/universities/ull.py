from __future__ import annotations

from .base import UniversitySiteMemoryResolver


class ULLMemoryResolver(UniversitySiteMemoryResolver):
    def __init__(self) -> None:
        super().__init__(
            university_id="ull",
            seed_url="https://www.ull.es/",
            search_paths=(
                "/",
                "/grados/",
                "/masters/",
                "/doctorados/",
                "/calidad/",
                "/sitemap.xml",
            ),
            link_markers=("memoria", "verificacion", "verifica"),
        )
