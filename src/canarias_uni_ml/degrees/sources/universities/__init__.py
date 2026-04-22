from .base import MemoryResolution, StaticHtmlMemoryResolver, UniversityMemoryResolver
from .uam import UAMMemoryResolver
from .uec import UECMemoryResolver
from .ufpc import UFPCMemoryResolver
from .ull import ULLMemoryResolver
from .ulpgc import ULPGCMemoryResolver

__all__ = [
    "MemoryResolution",
    "StaticHtmlMemoryResolver",
    "UniversityMemoryResolver",
    "ULLMemoryResolver",
    "ULPGCMemoryResolver",
    "UECMemoryResolver",
    "UAMMemoryResolver",
    "UFPCMemoryResolver",
]
