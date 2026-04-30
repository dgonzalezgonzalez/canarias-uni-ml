from __future__ import annotations

from .base import UniversitySiteMemoryResolver


class UECMemoryResolver(UniversitySiteMemoryResolver):
    def __init__(self) -> None:
        super().__init__(
            university_id="uec",
            seed_url="https://universidadeuropea.com/canarias/",
            search_paths=(
                "/canarias/",
                "/canarias/grados/",
                "/canarias/masteres-y-postgrados/",
                "/canarias/doctorados/",
                "/canarias/calidad-academica/",
                "/sitemap.xml",
            ),
            link_markers=("memoria", "verificacion", "verifica"),
        )
