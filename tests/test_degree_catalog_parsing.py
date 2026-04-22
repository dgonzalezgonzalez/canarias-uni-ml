from pathlib import Path

from src.canarias_uni_ml.degrees.catalog import build_degree_catalog, load_degree_catalog_from_fixture
from src.canarias_uni_ml.degrees.report_extract import build_description_from_report_text
from src.canarias_uni_ml.degrees.sources.aneca import parse_aneca_detail_page, parse_aneca_search_page


def test_degree_catalog_dedupes_same_degree():
    fixture = Path("tests/fixtures/degrees_catalog_fixture.json")
    payload = load_degree_catalog_from_fixture(str(fixture))
    records = build_degree_catalog(payload)
    assert len(records) == 2
    titles = {(record.university, record.title) for record in records}
    assert ("Universidad de La Laguna", "Grado en Ingeniería Informática") in titles
    assert ("Universidad de Las Palmas de Gran Canaria", "Grado en Turismo") in titles


def test_parse_aneca_search_page_extracts_grado_rows():
    html = """
    <ol class="search-results">
      <li class="search-result">
        <div id="imagen-lupa"><a href="/ListadoTitulos/node/1029523971"></a></div>
        <div class="resultado">
          <div class="info-basica-titulo">
            <h3 class="title">Grado en Matemáticas</h3>
            <div class="search-snippet-info"><ul class="search-snippet"><li>Universidad de Salamanca</li></ul></div>
          </div>
          <div class="detalles-titulo">
            <dt>Rama:</dt><dd>Ciencias</dd>
            <dt>Idioma de impartición:</dt><dd>Español</dd>
          </div>
        </div>
      </li>
    </ol>
    """
    rows = parse_aneca_search_page(html)
    assert rows == [{
        "title": "Grado en Matemáticas",
        "university": "Universidad de Salamanca",
        "branch": "Ciencias",
        "language": "Español",
        "source_url": "https://srv.aneca.es/ListadoTitulos/node/1029523971",
    }]


def test_parse_aneca_detail_page_extracts_report_and_metadata():
    html = """
    <html><body>
    <h1>Grado en Matemáticas</h1>
    <h2>Universidad de Salamanca</h2>
    <h2>Facultad de Ciencias (Salamanca)</h2>
    <h2>Ciencias</h2>
    <dl>
      <dt>Créditos ECTS:</dt><dd>240.00</dd>
      <dt>Idioma de impartición:</dt><dd>Español</dd>
    </dl>
    <table>
      <tr><th>Tipo</th><th>Descargar</th><th>Año</th></tr>
      <tr>
        <td>Evaluación</td>
        <td><a href="/ListadoTitulos/sites/default/files/informes/verificacion/InformeFinal_166-2008.pdf">pdf</a></td>
        <td>2008</td>
      </tr>
    </table>
    </body></html>
    """
    detail = parse_aneca_detail_page(html, "https://srv.aneca.es/ListadoTitulos/node/1029523971")
    assert detail["university"] == "Universidad de Salamanca"
    assert detail["center"] == "Facultad de Ciencias (Salamanca)"
    assert detail["branch"] == "Ciencias"
    assert detail["credits"] == "240.00"
    assert detail["language"] == "Español"
    assert detail["status"] == "Evaluación"
    assert detail["report_url"].endswith("InformeFinal_166-2008.pdf")


def test_build_description_from_report_text_extracts_motivacion():
    text = """
    Encabezado
    MOTIVACIÓN
    Descripción del Título. Recoge una descripción del plan de estudios adecuada.
    Justificación. Aporta evidencias de interés académico.
    RECOMENDACIONES
    Fin.
    """
    description = build_description_from_report_text(text)
    assert description is not None
    assert "Descripción del Título" in description
    assert "RECOMENDACIONES" not in description
