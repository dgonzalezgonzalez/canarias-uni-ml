from .base import (
    MemoryResolution,
    StaticHtmlMemoryResolver,
    UniversityMemoryResolver,
    UniversitySiteMemoryResolver,
    unresolved_resolution,
)
from .uam import UAMMemoryResolver
from .uec import UECMemoryResolver
from .ufpc import UFPCMemoryResolver
from .ull import ULLMemoryResolver
from .ulpgc import ULPGCMemoryResolver

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
]
