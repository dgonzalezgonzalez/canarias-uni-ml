from .base import SpiderError
from .indeed import IndeedSpider
from .infojobs import InfoJobsSpider
from .sce import SCESpider
from .turijobs import TurijobsSpider

__all__ = [
    "IndeedSpider",
    "InfoJobsSpider",
    "SCESpider",
    "SpiderError",
    "TurijobsSpider",
]
