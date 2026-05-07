from src.canarias_uni_ml.alignment.pairing import build_candidate_pairs


def test_pairing_uses_target_titles_and_branches():
    jobs = [
        {
            "source": "sce",
            "external_id": "1",
            "title": "Desarrollador",
            "description": "Buscamos perfil de software y backend con experiencia",
            "degree_match_status": "matched",
            "target_degree_titles": "Grado en Ingenieria Informatica",
            "target_degree_branches": "Ingenieria y Arquitectura",
        }
    ]
    degrees = [
        {
            "source": "catalog",
            "source_id": "d1",
            "title": "Grado en Ingenieria Informatica",
            "branch": "Ingenieria y Arquitectura",
            "description": "Programa de informatica aplicada al desarrollo de software",
        },
        {
            "source": "catalog",
            "source_id": "d2",
            "title": "Grado en Turismo",
            "branch": "Ciencias Sociales y Juridicas",
            "description": "Programa orientado al sector turistico",
        },
    ]
    pairs = build_candidate_pairs(jobs, degrees, min_text_len=10)
    assert len(pairs) == 1
    assert "informatica" in pairs[0].degree_text.lower()
    assert pairs[0].job_title == "Desarrollador"
    assert pairs[0].degree_title == "Grado en Ingenieria Informatica"


def test_pairing_skips_unmatched_jobs():
    jobs = [{"title": "X", "description": "texto suficiente", "degree_match_status": "no_rule"}]
    degrees = [{"title": "Grado", "description": "texto suficiente", "branch": "B"}]
    assert build_candidate_pairs(jobs, degrees, min_text_len=5) == []


def test_pairing_expands_same_degree_family_variants():
    jobs = [
        {
            "source": "jobspy_indeed",
            "external_id": "abc",
            "title": "Psicólogo/a clínico",
            "description": "Puesto para psicología con atención clínica y evaluación.",
            "degree_match_status": "matched",
            "target_degree_titles": "Grado en Psicología",
            "target_degree_branches": "Ciencias de la Salud|Ciencias Sociales y Juridicas",
        }
    ]
    degrees = [
        {
            "source": "catalog",
            "source_id": "psy_ull",
            "title": "Grado en Psicología",
            "branch": "Ciencias de la Salud",
            "description": "Formación en evaluación e intervención psicológica.",
        },
        {
            "source": "catalog",
            "source_id": "psy_online",
            "title": "Grado en Psicología online",
            "branch": "Ciencias de la Salud",
            "description": "Psicología aplicada con itinerario online.",
        },
        {
            "source": "catalog",
            "source_id": "psy_uam",
            "title": "Grado en Psicología - Presencial Duración: 4 años",
            "branch": "Ciencias de la Salud",
            "description": "Psicología presencial con prácticas.",
        },
        {
            "source": "catalog",
            "source_id": "tur",
            "title": "Grado en Turismo",
            "branch": "Ciencias Sociales y Juridicas",
            "description": "Sector turístico.",
        },
    ]
    pairs = build_candidate_pairs(jobs, degrees, min_text_len=10)
    titles = {pair.degree_title for pair in pairs}
    assert "Grado en Psicología" in titles
    assert "Grado en Psicología online" in titles
    assert "Grado en Psicología - Presencial Duración: 4 años" in titles
    assert "Grado en Turismo" not in titles
