from .base import BaseDimension
from .peak_pressure import PeakPressure
from .sustained_pressure import SustainedPressure
from .technique_complexity import TechniqueComplexity
from .rhythm_complexity import RhythmComplexity
from .reading_complexity import ReadingComplexity
from .accuracy_pressure import AccuracyPressure
from .miss_penalty import MissPenalty


def get_all_dimensions() -> list[BaseDimension]:
    """返回全部七个基础维度实例（按标准顺序）。"""
    return [
        PeakPressure(),
        SustainedPressure(),
        TechniqueComplexity(),
        RhythmComplexity(),
        ReadingComplexity(),
        AccuracyPressure(),
        MissPenalty(),
    ]


__all__ = [
    "BaseDimension",
    "PeakPressure", "SustainedPressure", "TechniqueComplexity",
    "RhythmComplexity", "ReadingComplexity", "AccuracyPressure",
    "MissPenalty",
    "get_all_dimensions",
]
