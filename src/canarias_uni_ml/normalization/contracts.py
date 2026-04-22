from __future__ import annotations

from ..jobs.utils import clean_text
from .models import ContractNormalization


CANONICAL_CONTRACT_TYPES = {
    "indefinido": {"indefinido", "contrato indefinido", "fijo", "permanent", "full time permanent"},
    "temporal": {"temporal", "contrato temporal", "eventual", "duracion determinada"},
    "formacion": {"formacion", "practicas", "beca", "internship", "aprendizaje"},
    "fijo_discontinuo": {"fijo discontinuo", "fijo-discontinuo"},
    "autonomo": {"autonomo", "freelance", "contract", "contratista"},
}


def normalize_contract_type(value: str | None) -> ContractNormalization:
    cleaned = (clean_text(value) or "").lower()
    if not cleaned:
        return ContractNormalization(contract_type=None, confidence="missing")
    for canonical, aliases in CANONICAL_CONTRACT_TYPES.items():
        if cleaned in aliases:
            return ContractNormalization(contract_type=canonical, confidence="exact")
    if "indefin" in cleaned:
        return ContractNormalization(contract_type="indefinido", confidence="alias")
    if "tempor" in cleaned or "sustit" in cleaned:
        return ContractNormalization(contract_type="temporal", confidence="alias")
    if "practi" in cleaned or "beca" in cleaned or "intern" in cleaned:
        return ContractNormalization(contract_type="formacion", confidence="alias")
    if "autonom" in cleaned or "freelance" in cleaned:
        return ContractNormalization(contract_type="autonomo", confidence="alias")
    return ContractNormalization(contract_type="other", confidence="unresolved")
