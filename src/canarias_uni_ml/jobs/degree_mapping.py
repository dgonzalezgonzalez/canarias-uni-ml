from __future__ import annotations

import csv
import re
import unicodedata
from dataclasses import dataclass, replace
from pathlib import Path

from .models import JobRecord
from .utils import clean_text

DEFAULT_DEGREES_CATALOG_PATH = Path("data/processed/degrees_catalog.csv")
CANDIDATE_SCORE_DELTA = 0.15
CANDIDATE_SCORE_MIN = 0.20
CANDIDATE_MAX_KEEP = 8


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
        titles=("Grado en Periodismo", "Grado en Comunicacion"),
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
    branch_by_title_norm: dict[str, str]

    @classmethod
    def from_csv(cls, path: Path) -> "DegreeCatalogIndex":
        title_by_norm: dict[str, str] = {}
        branch_by_norm: dict[str, str] = {}
        branch_by_title_norm: dict[str, str] = {}
        if not path.exists():
            return cls(title_by_norm=title_by_norm, branch_by_norm=branch_by_norm, branch_by_title_norm=branch_by_title_norm)
        with open(path, encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                title = clean_text(row.get("title"))
                branch = clean_text(row.get("branch"))
                if title:
                    title_norm = _norm(title)
                    title_by_norm.setdefault(title_norm, title)
                    if branch:
                        branch_by_title_norm.setdefault(title_norm, branch)
                if branch:
                    branch_by_norm.setdefault(_norm(branch), branch)
        return cls(title_by_norm=title_by_norm, branch_by_norm=branch_by_norm, branch_by_title_norm=branch_by_title_norm)

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
        explicit_titles: list[str] = []
        explicit_branches: list[str] = []

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
                _append_unique(explicit_branches, resolved_branch)
            for candidate_title in rule.titles:
                resolved_title = index.resolve_title(candidate_title) or candidate_title
                _append_unique(explicit_titles, resolved_title)

        scored = _score_catalog_titles(
            job_title_norm=title_only,
            all_job_text_norm=text_all,
            index=index,
            explicit_titles=explicit_titles,
            explicit_branches=explicit_branches,
        )

        selected = _select_titles(scored)
        selected_titles = [item["title"] for item in selected]
        selected_branches: list[str] = []
        for title in selected_titles:
            branch = index.branch_by_title_norm.get(_norm(title))
            if branch:
                _append_unique(selected_branches, branch)

        status = "matched" if selected_titles else "no_match"
        enriched.append(
            replace(
                record,
                target_degree_branches=_pipe_join(selected_branches),
                target_degree_titles=_pipe_join(selected_titles),
                degree_match_status=status,
            )
        )
    return enriched


def _score_catalog_titles(
    *,
    job_title_norm: str,
    all_job_text_norm: str,
    index: DegreeCatalogIndex,
    explicit_titles: list[str],
    explicit_branches: list[str],
) -> list[dict[str, float | str]]:
    explicit_title_norms = {_norm(title) for title in explicit_titles}
    explicit_branch_norms = {_norm(branch) for branch in explicit_branches}
    rows: list[dict[str, float | str]] = []

    for title_norm, title in index.title_by_norm.items():
        base = _title_similarity(job_title_norm, title_norm)
        if base <= 0.0 and not explicit_titles and not explicit_branches:
            continue

        bonus = 0.0
        if title_norm in explicit_title_norms:
            bonus += 0.30
        title_branch_norm = _norm(index.branch_by_title_norm.get(title_norm, ""))
        if title_branch_norm and title_branch_norm in explicit_branch_norms:
            bonus += 0.10
        if all_job_text_norm and title_norm in all_job_text_norm:
            bonus += 0.10

        score = min(1.0, base + bonus)
        rows.append({"title": title, "score": score})

    rows.sort(key=lambda x: (-float(x["score"]), str(x["title"])))
    return rows


def _select_titles(scored: list[dict[str, float | str]]) -> list[dict[str, float | str]]:
    if not scored:
        return []
    best_score = float(scored[0]["score"])
    if best_score < CANDIDATE_SCORE_MIN:
        return []
    cutoff = best_score - CANDIDATE_SCORE_DELTA
    kept = [row for row in scored if float(row["score"]) >= cutoff]
    return kept[:CANDIDATE_MAX_KEEP]


def _title_similarity(job_title_norm: str, degree_title_norm: str) -> float:
    job_tokens = _tokenize(job_title_norm)
    degree_tokens = _tokenize(degree_title_norm)
    if not job_tokens or not degree_tokens:
        return 0.0
    overlap = 0
    for dtoken in degree_tokens:
        if any(_token_match(dtoken, jtoken) for jtoken in job_tokens):
            overlap += 1
    return overlap / max(len(degree_tokens), 1)


def _tokenize(text: str) -> list[str]:
    if not text:
        return []
    stop = {"grado", "en", "de", "la", "el", "los", "las", "y", "del", "un", "una"}
    return [tok for tok in text.split() if tok and tok not in stop]


def _token_match(a: str, b: str) -> bool:
    if a == b:
        return True
    if len(a) >= 5 and len(b) >= 5:
        return a.startswith(b[:5]) or b.startswith(a[:5])
    return False


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
