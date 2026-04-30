from pathlib import Path

from src.canarias_uni_ml.degrees.sources.university_official import (
    extract_program_links_from_index,
    infer_title_type,
)


def test_extract_program_links_from_index_keeps_study_links():
    html = """
    <html><body>
      <a href="/grados/grado-en-enfermeria/">Grado en Enfermería</a>
      <a href="/masteres/master-en-educacion/">Máster en Educación</a>
      <a href="/blog/noticia-x">Noticia</a>
    </body></html>
    """
    rows = extract_program_links_from_index(html, page_url="https://uni.example")
    urls = {row["source_url"] for row in rows}
    assert "https://uni.example/grados/grado-en-enfermeria/" in urls
    assert "https://uni.example/masteres/master-en-educacion/" in urls
    assert "https://uni.example/blog/noticia-x" not in urls


def test_extract_program_links_from_index_rejects_known_slop_rows():
    html = Path("tests/fixtures/university_official/slop_links.html").read_text(encoding="utf-8")
    rows = extract_program_links_from_index(html, page_url="https://www.ull.es")
    titles = {row["title"] for row in rows}

    assert "Grado en Bellas Artes" in titles
    assert "Doble Grado en Bellas Artes y en Diseño" in titles
    assert "Inicio" not in titles
    assert "Listado Doctorados" not in titles
    assert "Criterios de Acceso y admisión" not in titles
    assert "SOLICITUD DE ADMISIÓN" not in titles
    assert "MATRÍCULA" not in titles


def test_extract_program_links_from_index_rejects_pdf_and_mailto_rows():
    html = """
    <html><body>
      <a href="/sites/default/files/masteres/folleto.pdf">Folleto informativo</a>
      <a href="mailto:doctorado@ull.es">doctorado@ull.es</a>
      <a href="/doctorados/quimica/">Programa de Doctorado en Química</a>
    </body></html>
    """
    rows = extract_program_links_from_index(html, page_url="https://uni.example")
    titles = {row["title"] for row in rows}

    assert titles == {"Programa de Doctorado en Química"}


def test_infer_title_type_detects_cycles():
    assert infer_title_type("Grado en Ingeniería") == "grado"
    assert infer_title_type("Máster en IA") == "master"
    assert infer_title_type("Programa de doctorado en química") == "doctorado"
