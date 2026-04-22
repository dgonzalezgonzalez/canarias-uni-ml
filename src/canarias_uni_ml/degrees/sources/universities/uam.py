from __future__ import annotations

from .base import UniversitySiteMemoryResolver


class UAMMemoryResolver(UniversitySiteMemoryResolver):
    def __init__(self) -> None:
        super().__init__(
            university_id="uam",
            seed_url="https://www.universidadatlanticomedio.es/",
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
