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


def test_pairing_skips_unmatched_jobs():
    jobs = [{"title": "X", "description": "texto suficiente", "degree_match_status": "no_rule"}]
    degrees = [{"title": "Grado", "description": "texto suficiente", "branch": "B"}]
    assert build_candidate_pairs(jobs, degrees, min_text_len=5) == []
