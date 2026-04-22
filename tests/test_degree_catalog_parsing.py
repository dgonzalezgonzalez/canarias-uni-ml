from pathlib import Path

from src.canarias_uni_ml.degrees.catalog import build_degree_catalog, load_degree_catalog_from_fixture


def test_degree_catalog_dedupes_same_degree():
    fixture = Path("tests/fixtures/degrees_catalog_fixture.json")
    payload = load_degree_catalog_from_fixture(str(fixture))
    records = build_degree_catalog(payload)
    assert len(records) == 2
    titles = {(record.university, record.title) for record in records}
    assert ("Universidad de La Laguna", "Grado en Ingeniería Informática") in titles
    assert ("Universidad de Las Palmas de Gran Canaria", "Grado en Turismo") in titles
