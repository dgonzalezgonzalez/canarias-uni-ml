from pathlib import Path
import unicodedata

from src.canarias_uni_ml.jobs.degree_mapping import annotate_job_degree_targets
from src.canarias_uni_ml.jobs.models import JobRecord


def _norm_text(value: str) -> str:
    lowered = value.lower()
    return "".join(
        c for c in unicodedata.normalize("NFD", lowered) if unicodedata.category(c) != "Mn"
    )


def _job(title: str, description: str = "") -> JobRecord:
    return JobRecord(
        source="sce",
        external_id="x",
        title=title,
        company=None,
        description=description,
        salary_text=None,
        salary_min=None,
        salary_max=None,
        salary_currency=None,
        salary_period=None,
        publication_date=None,
        update_date=None,
        source_url="https://example.org/x",
        scraped_at=JobRecord.now(),
    )


def test_degree_mapping_can_return_no_match_for_weak_signal(tmp_path):
    catalog = tmp_path / "degrees_catalog.csv"
    catalog.write_text(
        "\n".join(
            [
                "title,branch,description",
                "Grado en Enfermeria,Ciencias de la Salud,Cuidados de salud",
                "Grado en Ingenieria Informatica,Ingenieria y Arquitectura,Sistemas de software",
                "Grado en Turismo,Ciencias Sociales y Juridicas,Gestion turistica",
            ]
        ),
        encoding="utf-8",
    )
    jobs = [_job("Personal de limpieza")]
    mapped = annotate_job_degree_targets(jobs, degrees_catalog_path=catalog)

    assert mapped[0].target_degree_titles in (None, "")
    assert mapped[0].degree_match_status == "no_match"


def test_degree_mapping_prefers_rule_title_for_software_jobs():
    jobs = [_job("Desarrollador backend", "perfil software y desarrollo web")]
    mapped = annotate_job_degree_targets(
        jobs,
        degrees_catalog_path=Path("data/processed/degrees_catalog.csv"),
    )
    titles = set(filter(None, (mapped[0].target_degree_titles or "").split("|")))
    normalized_titles = [_norm_text(title) for title in titles]
    assert any(
        ("informatic" in title) or ("desarrollo web" in title) or ("videojuegos" in title)
        for title in normalized_titles
    )
    assert mapped[0].degree_match_status == "matched"


def test_degree_mapping_science_teacher_excludes_unrelated_titles():
    jobs = [_job("Profesor de Física, Química y Ciencias")]
    mapped = annotate_job_degree_targets(
        jobs,
        degrees_catalog_path=Path("data/processed/degrees_catalog.csv"),
    )

    titles = set(filter(None, (mapped[0].target_degree_titles or "").split("|")))
    assert mapped[0].degree_match_status == "matched"
    assert titles

    unrelated = {
        "Grado en Bellas Artes",
        "Grado en Espanol",
        "Grado en Lengua Espanola y Literatura Hispanica",
        "Grado en Filologia Hispanica",
    }
    assert titles.isdisjoint(unrelated)


def test_degree_mapping_electrician_penalizes_non_technical_degrees(tmp_path):
    catalog = tmp_path / "degrees_catalog.csv"
    catalog.write_text(
        "\n".join(
            [
                "title,branch,description",
                "Grado en Ingenieria Electrica,Ingenieria y Arquitectura,Sistemas electricos e instalaciones",
                "Grado en Psicologia,Ciencias Sociales y Juridicas,Conducta humana y salud mental",
                "Master en Violencia de Genero,Ciencias Sociales y Juridicas,Intervencion social y politicas publicas",
            ]
        ),
        encoding="utf-8",
    )
    jobs = [_job("Electricista de instalaciones", "montaje electrico baja tension")]
    mapped = annotate_job_degree_targets(jobs, degrees_catalog_path=catalog)
    titles = set(filter(None, (mapped[0].target_degree_titles or "").split("|")))

    assert "Grado en Ingenieria Electrica" in titles
    assert "Grado en Psicologia" not in titles
    assert "Master en Violencia de Genero" not in titles


def test_degree_mapping_has_deterministic_order_for_ties(tmp_path):
    catalog = tmp_path / "degrees_catalog.csv"
    catalog.write_text(
        "\n".join(
            [
                "title,branch,description",
                "Grado en A,Ciencias,formacion a",
                "Grado en B,Ciencias,formacion b",
            ]
        ),
        encoding="utf-8",
    )
    jobs = [_job("A B")]
    first = annotate_job_degree_targets(jobs, degrees_catalog_path=catalog)[0].target_degree_titles
    second = annotate_job_degree_targets(jobs, degrees_catalog_path=catalog)[0].target_degree_titles
    assert first == second


def test_degree_mapping_caps_selected_titles_to_max_keep(tmp_path):
    lines = ["title,branch,description"]
    for idx in range(1, 13):
        lines.append(f"Grado en Ingenieria {idx},Ingenieria y Arquitectura,ingenieria aplicada {idx}")
    catalog = tmp_path / "degrees_catalog.csv"
    catalog.write_text("\n".join(lines), encoding="utf-8")
    jobs = [_job("Ingeniero de proyectos", "ingenieria tecnica")]
    mapped = annotate_job_degree_targets(jobs, degrees_catalog_path=catalog)
    titles = list(filter(None, (mapped[0].target_degree_titles or "").split("|")))
    assert len(titles) <= 5
