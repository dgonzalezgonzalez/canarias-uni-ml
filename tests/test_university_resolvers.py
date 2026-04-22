from pathlib import Path

from src.canarias_uni_ml.degrees.sources.universities.uam import UAMMemoryResolver
from src.canarias_uni_ml.degrees.sources.universities.uec import UECMemoryResolver
from src.canarias_uni_ml.degrees.sources.universities.ufpc import UFPCMemoryResolver
from src.canarias_uni_ml.degrees.sources.universities.ull import ULLMemoryResolver
from src.canarias_uni_ml.degrees.sources.universities.ulpgc import ULPGCMemoryResolver


def _fixture(name: str) -> str:
    return Path(f"tests/fixtures/university_memory_samples/{name}.html").read_text(encoding="utf-8")


def test_ull_resolver_extracts_memory_link_from_html():
    result = ULLMemoryResolver().resolve_from_html(_fixture("ull"))
    assert result.status == "resolved"
    assert result.memory_url is not None
    assert result.memory_url.endswith("memoria-verificacion-grado-informatica.pdf")


def test_ulpgc_resolver_extracts_absolute_link_from_html():
    result = ULPGCMemoryResolver().resolve_from_html(_fixture("ulpgc"))
    assert result.status == "resolved"
    assert result.memory_url == "https://www.ulpgc.es/storage/memorias/master-ciberseguridad.pdf"


def test_other_resolvers_match_expected_patterns():
    assert UECMemoryResolver().resolve_from_html(_fixture("uec")).status == "resolved"
    assert UAMMemoryResolver().resolve_from_html(_fixture("uam")).status == "resolved"
    assert UFPCMemoryResolver().resolve_from_html(_fixture("ufpc")).status == "resolved"
