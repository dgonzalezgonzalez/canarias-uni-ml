from __future__ import annotations

import re
import unicodedata
from urllib.parse import urlparse

TITLE_TYPE_MARKERS = {
    "grado": ("grado", "grados", "degree", "bachelor"),
    "master": ("master", "masters", "máster", "másteres", "postgrado", "postgraduates"),
    "doctorado": ("doctorado", "doctorados", "phd", "doctoral"),
}

TITLE_PATTERNS = {
    "grado": (
        re.compile(r"^(doble\s+)?grado\s+(en|de|:)", re.I),
        re.compile(r"^(doble\s+)?grado\s+[a-z0-9áéíóúñ]", re.I),
        re.compile(r"^carrera\s+de\s+", re.I),
        re.compile(r"^bachelor", re.I),
        re.compile(r"^degree\s+in\s+", re.I),
    ),
    "master": (
        re.compile(r"^m[aá]ster(\s+universitario)?\s+(en|de|:)", re.I),
        re.compile(r"^master\s+in\s+", re.I),
        re.compile(r"^postgrado\s+de\s+", re.I),
    ),
    "doctorado": (
        re.compile(r"^(programa\s+de\s+)?doctorado\s+(en|de|:)", re.I),
        re.compile(r"^doctoral\s+program", re.I),
    ),
}

NEGATIVE_TITLE_MARKERS = {
    "inicio",
    "listado",
    "criterios de acceso",
    "acceso y admision",
    "acceso y admisión",
    "solicitud",
    "matricula",
    "matrícula",
    "calendario",
    "examen",
    "practicas externas",
    "prácticas externas",
    "registro de actividades",
    "reconocimiento",
    "premios extraordinarios",
    "movilidad internacional",
    "normativa",
    "estadisticas",
    "estadísticas",
    "change language",
    "folleto informativo",
    "programme's brochure",
    "brochure",
    "web del titulo",
    "web del título",
    "asignaturas",
    "horarios",
    "otra informacion",
    "otra información",
    "directorio",
    "administracion de masteres",
    "administración de másteres",
    "ver todos",
    "explora mas",
    "explora más",
    "solicita informacion",
    "solicita información",
}

NEGATIVE_URL_MARKERS = (
    "blog",
    "noticia",
    "news",
    "event",
    "contact",
    "legal",
    "privacy",
    "sitemap",
    "admision",
    "admisiones",
    "matricula",
    "calendario",
    "examen",
    "practicas",
    "normativa",
    "estadisticas",
)

GENERIC_TITLES = {
    "grado",
    "grados",
    "grados universitarios",
    "grado universitario",
    "master",
    "masters",
    "máster",
    "másteres",
    "masteres",
    "másteres oficiales",
    "doctorado",
    "doctorados",
    "titulaciones de grado",
    "titulaciones de master universitario",
    "titulaciones de máster universitario",
    "estudios",
}


def infer_title_type(text: str | None) -> str | None:
    value = normalize_for_match(text)
    if not value:
        return None
    for cycle, markers in TITLE_TYPE_MARKERS.items():
        if any(marker in value for marker in markers):
            return cycle
    return None


def is_program_title(title: str | None, title_type: str | None = None) -> bool:
    normalized = normalize_for_match(title)
    if not normalized or len(normalized) < 8:
        return False
    if normalized in GENERIC_TITLES:
        return False
    if any(marker in normalized for marker in NEGATIVE_TITLE_MARKERS):
        return False
    candidate_type = title_type or infer_title_type(title)
    if not candidate_type:
        return False
    return any(pattern.search(title or "") for pattern in TITLE_PATTERNS.get(candidate_type, ()))


def is_allowed_program_url(url: str | None, *, allow_pdf: bool = False) -> bool:
    if not url:
        return False
    parsed = urlparse(url)
    if parsed.scheme in {"mailto", "tel"}:
        return False
    path = (parsed.path or "").lower().rstrip("/")
    if not path:
        return False
    if path.endswith(".pdf") and not allow_pdf:
        return False
    return not any(marker in path for marker in NEGATIVE_URL_MARKERS)


def is_valid_program_candidate(title: str | None, url: str | None, title_type: str | None = None) -> bool:
    return is_program_title(title, title_type) and is_allowed_program_url(url)


def normalize_for_match(text: str | None) -> str:
    if not text:
        return ""
    normalized = unicodedata.normalize("NFD", text)
    no_accents = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    return " ".join(no_accents.lower().split())
