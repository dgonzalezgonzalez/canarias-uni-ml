from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class GeographyNormalization:
    province: str | None
    municipality: str | None
    island: str | None
    raw_location: str | None
    confidence: str


@dataclass(slots=True)
class ContractNormalization:
    contract_type: str | None
    confidence: str
