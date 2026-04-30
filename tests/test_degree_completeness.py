from src.canarias_uni_ml.degrees.completeness import (
    compute_inventory_completeness,
    ensure_min_inventory_completeness,
    validate_degree_catalog_quality,
)


def test_compute_inventory_completeness_counts_universities_and_title_types():
    rows = [
        {"university_id": "ull", "title_type": "grado"},
        {"university_id": "ulpgc", "title_type": "master"},
        {"university_id": "uhesp", "title_type": "doctorado"},
    ]
    completeness = compute_inventory_completeness(
        rows,
        required_university_ids=("ull", "ulpgc", "uhesp"),
        required_title_types=("grado", "master", "doctorado"),
    )
    assert completeness.expected_universities == 3
    assert completeness.observed_universities == 3
    assert completeness.university_ratio == 1.0
    assert completeness.missing_university_ids == ()
    assert completeness.title_type_ratio == 1.0
    assert completeness.missing_title_types == ()
    assert ("ull", "master") in completeness.missing_university_title_type_pairs


def test_compute_inventory_completeness_reports_missing_scope():
    rows = [
        {"university_id": "ull", "title_type": "grado"},
        {"university_id": "ull", "title_type": "master"},
    ]
    completeness = compute_inventory_completeness(
        rows,
        required_university_ids=("ull", "ulpgc"),
        required_title_types=("grado", "master", "doctorado"),
    )
    assert completeness.university_ratio == 0.5
    assert completeness.missing_university_ids == ("ulpgc",)
    assert completeness.title_type_ratio == 2 / 3
    assert completeness.missing_title_types == ("doctorado",)
    assert ("ulpgc", "grado") in completeness.missing_university_title_type_pairs
    assert ("ulpgc", "master") in completeness.missing_university_title_type_pairs


def test_ensure_min_inventory_completeness_honors_scope_gate():
    rows = [
        {"university_id": "ull", "title_type": "grado"},
        {"university_id": "ulpgc", "title_type": "master"},
    ]
    ok, _ = ensure_min_inventory_completeness(
        rows,
        0.3,
        require_all_scoped_universities=False,
        required_title_types=("grado", "master"),
    )
    assert ok is True

    ok, _ = ensure_min_inventory_completeness(
        rows,
        0.5,
        require_all_scoped_universities=True,
        required_title_types=("grado", "master"),
    )
    assert ok is False


def test_validate_degree_catalog_quality_rejects_slop_titles_and_urls():
    rows = [
        {"title": "Grado en Historia", "title_type": "grado", "source_url": "https://www.ull.es/grados/historia/"},
        {"title": "Inicio", "title_type": "grado", "source_url": "https://www.ull.es/grados/"},
        {"title": "Folleto informativo", "title_type": "master", "source_url": "https://www.ulpgc.es/master.pdf"},
        {"title": "doctorado@ull.es", "title_type": "doctorado", "source_url": "mailto:doctorado@ull.es"},
        {"title": "Calendario académico", "title_type": "", "source_url": "https://www.ull.es/calendario"},
    ]
    quality = validate_degree_catalog_quality(rows)

    assert quality.ok is False
    assert len(quality.blocked_rows) == 4


def test_validate_degree_catalog_quality_accepts_real_programs():
    rows = [
        {
            "title": "Doble Grado en Bellas Artes y en Diseño",
            "title_type": "grado",
            "source_url": "https://www.ull.es/grados/bellas-artes-y-diseno/",
        },
        {
            "title": "Máster Universitario en Cultura Audiovisual y Literaria",
            "title_type": "master",
            "source_url": "https://www2.ulpgc.es/plan-estudio/5001",
        },
        {
            "title": "Programa de Doctorado en Química",
            "title_type": "doctorado",
            "source_url": "https://www.ull.es/doctorados/quimica/",
        },
    ]
    quality = validate_degree_catalog_quality(rows)

    assert quality.ok is True
