"""评定结果数据结构。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .enums import Course, BranchType, TargetDifficulty


CALC_VERSION = "0.1.0"


@dataclass
class Hotspot:
    """难点窗口。"""
    start_time: float               # 起始时间（秒）
    end_time: float                 # 结束时间（秒）
    severity: float                 # 严重程度 0‑1
    primary_dimensions: list[str]   # 主要贡献维度名
    affected_targets: list[TargetDifficulty]
    explanation: str = ""


@dataclass
class DimensionScore:
    """单个基础维度评分。"""
    name: str
    raw_value: float         # 原始计算值
    normalized: float        # 标准化分数 0‑10
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class WindowMetrics:
    """滑窗分析指标（段落级）。"""
    start_time: float
    end_time: float
    window_size: str         # "short" / "medium" / "long"
    instant_pressure: float = 0.0
    sustained_pressure: float = 0.0
    technique_complexity: float = 0.0
    rhythm_complexity: float = 0.0
    reading_complexity: float = 0.0
    accuracy_pressure: float = 0.0
    recovery_difficulty: float = 0.0

    def to_dict(self) -> dict[str, float]:
        return {
            "instant_pressure": self.instant_pressure,
            "sustained_pressure": self.sustained_pressure,
            "technique_complexity": self.technique_complexity,
            "rhythm_complexity": self.rhythm_complexity,
            "reading_complexity": self.reading_complexity,
            "accuracy_pressure": self.accuracy_pressure,
            "recovery_difficulty": self.recovery_difficulty,
        }


@dataclass
class BranchResult:
    """单分支评定结果。"""
    song_title: str
    course: Course
    branch_type: BranchType
    target_difficulties: dict[TargetDifficulty, float] = field(default_factory=dict)
    dimensions: list[DimensionScore] = field(default_factory=list)
    hotspots: list[Hotspot] = field(default_factory=list)
    window_metrics: list[WindowMetrics] = field(default_factory=list)
    summary: str = ""
    stats: dict[str, Any] = field(default_factory=dict)
    missing_fields: list[str] = field(default_factory=list)
    calc_version: str = CALC_VERSION

    def dimension_by_name(self, name: str) -> DimensionScore | None:
        for d in self.dimensions:
            if d.name == name:
                return d
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "song_title": self.song_title,
            "course": self.course.label,
            "branch_type": self.branch_type.value,
            "target_difficulties": {
                k.value: round(v, 4) for k, v in self.target_difficulties.items()
            },
            "dimensions": [
                {"name": d.name, "raw": round(d.raw_value, 4),
                 "normalized": round(d.normalized, 4), "details": d.details}
                for d in self.dimensions
            ],
            "hotspots": [
                {"start": round(h.start_time, 3), "end": round(h.end_time, 3),
                 "severity": round(h.severity, 4),
                 "primary_dimensions": h.primary_dimensions,
                 "affected_targets": [t.value for t in h.affected_targets],
                 "explanation": h.explanation}
                for h in self.hotspots
            ],
            "summary": self.summary,
            "stats": self.stats,
            "missing_fields": self.missing_fields,
            "calc_version": self.calc_version,
        }


@dataclass
class ChartResult:
    """单谱面评定结果（含所有分支）。"""
    song_title: str
    course: Course
    branch_results: list[BranchResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "song_title": self.song_title,
            "course": self.course.label,
            "branches": [br.to_dict() for br in self.branch_results],
        }


@dataclass
class SongResult:
    """歌曲级汇总结果。"""
    title: str
    chart_results: list[ChartResult] = field(default_factory=list)
    overview: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "charts": [cr.to_dict() for cr in self.chart_results],
            "overview": self.overview,
        }
