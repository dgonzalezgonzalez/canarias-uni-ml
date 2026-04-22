from src.canarias_uni_ml.degrees.memory_resolver import resolve_missing_memory
from src.canarias_uni_ml.degrees.models import DegreeCatalogRecord


def test_memory_resolver_returns_existing_url_without_lookup():
    record = DegreeCatalogRecord(
        source="aneca_live",
        source_id="1",
        university="Universidad de La Laguna",
        title="Grado en Ingenieria Informatica",
        university_id="ull",
        memory_url="https://example.org/memoria.pdf",
    )
    result = resolve_missing_memory(record)
    assert result.status == "already_present"
    assert result.memory_url == "https://example.org/memoria.pdf"


def test_memory_resolver_handles_missing_university_resolver():
    record = DegreeCatalogRecord(
        source="aneca_live",
        source_id="2",
        university="Universidad X",
        title="Doctorado en Prueba",
        university_id="unknown",
    )
    result = resolve_missing_memory(record)
    assert result.status == "unresolved"
    assert result.error == "no_resolver_for_university"
