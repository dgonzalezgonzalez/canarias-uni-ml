from .base import SpiderError
from .indeed import IndeedSpider
from .indeed_api import IndeedApiSpider
from .infojobs import InfoJobsSpider
from .sce import SCESpider
from .turijobs import TurijobsSpider

__all__ = [
    "IndeedApiSpider",
    "IndeedSpider",
    "InfoJobsSpider",
    "SCESpider",
    "SpiderError",
    "TurijobsSpider",
]
