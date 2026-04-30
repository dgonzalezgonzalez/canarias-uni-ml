from .base import (
    MemoryResolution,
    StaticHtmlMemoryResolver,
    UniversityMemoryResolver,
    UniversitySiteMemoryResolver,
    unresolved_resolution,
)
from .uam import UAMMemoryResolver
from .uam_programs import parse_uam_programs
from .uec import UECMemoryResolver
from .uec_programs import parse_uec_programs
from .ufpc import UFPCMemoryResolver
from .ufpc_programs import parse_ufpc_programs
from .uhesp import UHESPMemoryResolver
from .uhesp_programs import parse_uhesp_programs
from .ull import ULLMemoryResolver
from .ull_programs import parse_ull_programs
from .ulpgc import ULPGCMemoryResolver
from .ulpgc_programs import parse_ulpgc_programs

__all__ = [
    "MemoryResolution",
    "StaticHtmlMemoryResolver",
    "UniversitySiteMemoryResolver",
    "UniversityMemoryResolver",
    "unresolved_resolution",
    "ULLMemoryResolver",
    "ULPGCMemoryResolver",
    "UECMemoryResolver",
    "UAMMemoryResolver",
    "UFPCMemoryResolver",
    "UHESPMemoryResolver",
    "parse_ull_programs",
    "parse_ulpgc_programs",
    "parse_uec_programs",
    "parse_uam_programs",
    "parse_ufpc_programs",
    "parse_uhesp_programs",
]
