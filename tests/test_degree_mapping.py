from pathlib import Path

from src.canarias_uni_ml.jobs.degree_mapping import annotate_job_degree_targets
from src.canarias_uni_ml.jobs.models import JobRecord


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


def test_degree_mapping_guarantees_at_least_one_title(tmp_path):
    catalog = tmp_path / "degrees_catalog.csv"
    catalog.write_text(
        "\n".join(
            [
                "title,branch",
                "Grado en Enfermeria,Ciencias de la Salud",
                "Grado en Ingenieria Informatica,Ingenieria y Arquitectura",
                "Grado en Turismo,Ciencias Sociales y Juridicas",
            ]
        ),
        encoding="utf-8",
    )
    jobs = [
        _job("Personal de limpieza"),
        _job("Desarrollador backend", "perfil software"),
        _job("Auxiliar sanitario"),
    ]
    mapped = annotate_job_degree_targets(jobs, degrees_catalog_path=catalog)

    assert all((item.target_degree_titles or "").strip() for item in mapped)
    assert all(item.degree_match_status == "matched" for item in mapped)


def test_degree_mapping_uses_catalog_title_when_rule_title_missing():
    jobs = [_job("Docente de matemáticas")]
    mapped = annotate_job_degree_targets(
        jobs,
        degrees_catalog_path=Path("data/processed/degrees_catalog.csv"),
    )
    assert (mapped[0].target_degree_titles or "").strip()


def test_degree_mapping_expands_titles_from_same_branch(tmp_path):
    catalog = tmp_path / "degrees_catalog.csv"
    catalog.write_text(
        "\n".join(
            [
                "title,branch",
                "Grado en Turismo,Ciencias Sociales y Juridicas",
                "Grado en Derecho,Ciencias Sociales y Juridicas",
                "Grado en Medicina,Ciencias de la Salud",
            ]
        ),
        encoding="utf-8",
    )
    jobs = [_job("Técnico de turismo")]
    mapped = annotate_job_degree_targets(jobs, degrees_catalog_path=catalog)
    titles = set((mapped[0].target_degree_titles or "").split("|"))

    assert "Grado en Turismo" in titles
    assert "Grado en Derecho" in titles
