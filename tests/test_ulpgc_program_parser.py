from pathlib import Path

from src.canarias_uni_ml.degrees.sources.universities.ulpgc_programs import parse_ulpgc_programs


def test_ulpgc_master_parser_uses_headings_not_child_link_labels():
    html = Path("tests/fixtures/university_official/ulpgc_masteres.html").read_text(encoding="utf-8")
    rows = parse_ulpgc_programs(html, page_url="https://www.ulpgc.es/masteres", title_type="master")
    titles = {row.title for row in rows}

    assert "Máster Universitario en Cultura Audiovisual y Literaria" in titles
    assert "Máster Universitario en Oceanografía" in titles
    assert "Folleto informativo" not in titles
    assert "master@example.edu" not in titles


def test_ulpgc_parser_prefers_web_del_titulo_detail_url():
    html = Path("tests/fixtures/university_official/ulpgc_masteres.html").read_text(encoding="utf-8")
    rows = parse_ulpgc_programs(html, page_url="https://www.ulpgc.es/masteres", title_type="master")
    row = next(item for item in rows if item.title == "Máster Universitario en Cultura Audiovisual y Literaria")

    assert row.source_url == "https://www2.ulpgc.es/plan-estudio/5001"


def test_ulpgc_grade_parser_normalizes_doble_titulacion_heading():
    html = Path("tests/fixtures/university_official/ulpgc_grados.html").read_text(encoding="utf-8")
    rows = parse_ulpgc_programs(html, page_url="https://www.ulpgc.es/grados", title_type="grado")
    titles = {row.title for row in rows}

    assert "Grado en Historia" in titles
    assert "Doble Grado en Administración y Dirección de Empresas y Grado en Turismo" in titles
