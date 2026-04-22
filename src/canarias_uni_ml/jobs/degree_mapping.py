from __future__ import annotations

import csv
import re
import unicodedata
from dataclasses import dataclass, replace
from pathlib import Path

from .models import JobRecord
from .utils import clean_text

DEFAULT_DEGREES_CATALOG_PATH = Path("data/processed/degrees_catalog.csv")


@dataclass(frozen=True, slots=True)
class DegreeRule:
    name: str
    keywords: tuple[str, ...]
    branches: tuple[str, ...] = ()
    titles: tuple[str, ...] = ()
    scope: str = "all"  # "all" | "title"


DEGREE_RULES: tuple[DegreeRule, ...] = (
    DegreeRule(
        name="health_nursing",
        keywords=("enfermer",),
        branches=("Ciencias de la Salud",),
        titles=("Grado en Enfermeria",),
    ),
    DegreeRule(
        name="health_medicine",
        keywords=("medic", "facultativo"),
        branches=("Ciencias de la Salud",),
        titles=("Grado en Medicina",),
    ),
    DegreeRule(
        name="health_psychology",
        keywords=("psicolog",),
        branches=("Ciencias Sociales y Juridicas", "Ciencias de la Salud"),
        titles=("Grado en Psicologia",),
    ),
    DegreeRule(
        name="health_physiotherapy",
        keywords=("fisioterap",),
        branches=("Ciencias de la Salud",),
        titles=("Grado en Fisioterapia",),
    ),
    DegreeRule(
        name="health_dentistry",
        keywords=("odontolog", "dentista"),
        branches=("Ciencias de la Salud",),
        titles=("Grado en Odontologia",),
    ),
    DegreeRule(
        name="health_nutrition",
        keywords=("nutricion", "dietista"),
        branches=("Ciencias de la Salud",),
        titles=("Grado en Nutricion Humana y Dietetica",),
    ),
    DegreeRule(
        name="health_occupational_therapy",
        keywords=("terapia ocupacional", "terapeuta ocupacional"),
        branches=("Ciencias de la Salud",),
        titles=("Grado en Terapia Ocupacional",),
    ),
    DegreeRule(
        name="law",
        keywords=("abogad", "juridic", "asesor legal"),
        branches=("Ciencias Sociales y Juridicas",),
        titles=("Grado en Derecho",),
    ),
    DegreeRule(
        name="education",
        keywords=("maestro", "docente", "profesor", "profesora"),
        branches=("Ciencias Sociales y Juridicas",),
        titles=("Grado en Maestro en Educacion Infantil", "Grado en Maestro en Educacion Primaria"),
        scope="title",
    ),
    DegreeRule(
        name="education_science",
        keywords=("profesor", "profesora", "docente", "matematic", "fisic", "quimic", "biolog"),
        branches=("Ciencias",),
        scope="title",
    ),
    DegreeRule(
        name="data_science",
        keywords=("cientifico de datos", "data scientist", "analista de datos"),
        branches=("Ingenieria y Arquitectura", "Ciencias"),
        titles=("Grado en Ciencia e Ingenieria de Datos",),
    ),
    DegreeRule(
        name="software",
        keywords=("desarrollador", "developer", "programador", "software", "full stack", "backend", "frontend"),
        branches=("Ingenieria y Arquitectura",),
        titles=("Grado en Ingenieria Informatica",),
    ),
    DegreeRule(
        name="engineering_generic",
        keywords=("ingenier",),
        branches=("Ingenieria y Arquitectura",),
    ),
    DegreeRule(
        name="engineering_mechanical",
        keywords=("ingeniero mecanico", "ingenieria mecanica"),
        branches=("Ingenieria y Arquitectura",),
        titles=("Grado en Ingenieria Mecanica",),
    ),
    DegreeRule(
        name="engineering_electrical",
        keywords=("ingeniero electrico", "ingenieria electrica"),
        branches=("Ingenieria y Arquitectura",),
        titles=("Grado en Ingenieria Electrica",),
    ),
    DegreeRule(
        name="engineering_electronics",
        keywords=("ingeniero electronico", "ingenieria electronica"),
        branches=("Ingenieria y Arquitectura",),
        titles=("Grado en Ingenieria Electronica Industrial y Automatica",),
    ),
    DegreeRule(
        name="engineering_chemical",
        keywords=("ingeniero quimico", "ingenieria quimica"),
        branches=("Ingenieria y Arquitectura",),
        titles=("Grado en Ingenieria Quimica Industrial",),
    ),
    DegreeRule(
        name="tourism",
        keywords=("turismo",),
        branches=("Ciencias Sociales y Juridicas",),
        titles=("Grado en Turismo",),
        scope="title",
    ),
    DegreeRule(
        name="communication_periodism",
        keywords=("periodista", "periodismo", "comunicacion audiovisual"),
        branches=("Ciencias Sociales y Juridicas",),
        titles=("Grado en Periodismo", "Grado en Comunicacion",),
        scope="title",
    ),
    DegreeRule(
        name="economics",
        keywords=("economista", "economia", "finanzas"),
        branches=("Ciencias Sociales y Juridicas",),
        titles=("Grado en Economia",),
        scope="title",
    ),
    DegreeRule(
        name="business_admin",
        keywords=("administracion de empresas", "direccion de empresas", "business analyst"),
        branches=("Ciencias Sociales y Juridicas",),
        titles=("Grado en Administracion y Direccion de Empresas",),
        scope="title",
    ),
    DegreeRule(
        name="social_work",
        keywords=("trabajador social", "trabajo social"),
        branches=("Ciencias Sociales y Juridicas",),
        titles=("Grado en Trabajo Social",),
        scope="title",
    ),
)


@dataclass(slots=True)
class DegreeCatalogIndex:
    title_by_norm: dict[str, str]
    branch_by_norm: dict[str, str]

    @classmethod
    def from_csv(cls, path: Path) -> "DegreeCatalogIndex":
        title_by_norm: dict[str, str] = {}
        branch_by_norm: dict[str, str] = {}
        if not path.exists():
            return cls(title_by_norm=title_by_norm, branch_by_norm=branch_by_norm)
        with open(path, encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                title = clean_text(row.get("title"))
                branch = clean_text(row.get("branch"))
                if title:
                    title_by_norm.setdefault(_norm(title), title)
                if branch:
                    branch_by_norm.setdefault(_norm(branch), branch)
        return cls(title_by_norm=title_by_norm, branch_by_norm=branch_by_norm)

    def resolve_title(self, candidate: str) -> str | None:
        return self.title_by_norm.get(_norm(candidate))

    def resolve_branch(self, candidate: str) -> str | None:
        return self.branch_by_norm.get(_norm(candidate))


def annotate_job_degree_targets(
    records: list[JobRecord],
    *,
    degrees_catalog_path: str | Path = DEFAULT_DEGREES_CATALOG_PATH,
) -> list[JobRecord]:
    index = DegreeCatalogIndex.from_csv(Path(degrees_catalog_path))
    enriched: list[JobRecord] = []
    for record in records:
        titles: list[str] = []
        branches: list[str] = []
        text_all = _norm(" ".join(filter(None, [record.title or "", record.description or ""])))
        title_only = _norm(record.title or "")
        is_teaching_post = any(token in title_only for token in ("profesor", "profesora", "docente", "maestro"))
        for rule in DEGREE_RULES:
            haystack = title_only if rule.scope == "title" else text_all
            if not _rule_matches(haystack, rule.keywords):
                continue
            if is_teaching_post and rule.name in {
                "engineering_generic",
                "engineering_mechanical",
                "engineering_electrical",
                "engineering_electronics",
                "engineering_chemical",
                "software",
                "data_science",
            }:
                continue
            for candidate_branch in rule.branches:
                resolved_branch = index.resolve_branch(candidate_branch) or candidate_branch
                _append_unique(branches, resolved_branch)
            for candidate_title in rule.titles:
                resolved_title = index.resolve_title(candidate_title) or candidate_title
                _append_unique(titles, resolved_title)

        valid_titles = [title for title in titles if _is_valid_title(index, title)]
        valid_branches = [branch for branch in branches if _is_valid_branch(index, branch)]
        status = "matched" if valid_titles or valid_branches else "no_rule"
        enriched.append(
            replace(
                record,
                target_degree_branches=_pipe_join(valid_branches),
                target_degree_titles=_pipe_join(valid_titles),
                degree_match_status=status,
            )
        )
    return enriched


def _is_valid_title(index: DegreeCatalogIndex, title: str) -> bool:
    if not index.title_by_norm:
        return True
    return _norm(title) in index.title_by_norm


def _is_valid_branch(index: DegreeCatalogIndex, branch: str) -> bool:
    if not index.branch_by_norm:
        return True
    return _norm(branch) in index.branch_by_norm


def _norm(value: str) -> str:
    lowered = value.strip().lower()
    no_accents = "".join(
        char
        for char in unicodedata.normalize("NFD", lowered)
        if unicodedata.category(char) != "Mn"
    )
    no_punct = re.sub(r"[^a-z0-9\s]", " ", no_accents)
    return re.sub(r"\s+", " ", no_punct).strip()


def _rule_matches(text: str, keywords: tuple[str, ...]) -> bool:
    if not text:
        return False
    return any(_norm(keyword) in text for keyword in keywords)


def _append_unique(target: list[str], value: str) -> None:
    if value and value not in target:
        target.append(value)


def _pipe_join(values: list[str]) -> str | None:
    if not values:
        return None
    return "|".join(values)
