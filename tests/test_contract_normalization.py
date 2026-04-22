from src.canarias_uni_ml.normalization.contracts import normalize_contract_type


def test_contract_aliases_collapse():
    assert normalize_contract_type("INDEFINIDO").contract_type == "indefinido"
    assert normalize_contract_type("Indefinido").contract_type == "indefinido"
    assert normalize_contract_type("contrato indefinido").contract_type == "indefinido"


def test_unknown_contract_maps_other():
    result = normalize_contract_type("modalidad rara")
    assert result.contract_type == "other"
    assert result.confidence == "unresolved"


def test_clean_text_nan_becomes_none():
    from src.canarias_uni_ml.jobs.utils import clean_text
    assert clean_text(float("nan")) is None
    assert clean_text("nan") is None
