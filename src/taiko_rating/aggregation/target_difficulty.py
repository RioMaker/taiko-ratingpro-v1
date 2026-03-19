"""三类目标难度聚合。

基于七个基础维度，按不同权重和聚合方式生成：
  1. 过关难度 (pass)
  2. 全连难度 (fc)
  3. 高精度难度 (acc)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..models.enums import TargetDifficulty
from ..models.result import DimensionScore


@dataclass
class AggregationProfile:
    """单类目标难度的聚合配置。"""
    target: TargetDifficulty
    # 维度名 → 权重
    weights: dict[str, float]
    # 是否使用峰值加权（侧重最高分维度）
    peak_boost: float = 0.0
    description: str = ""


# ---- 默认聚合配置 ----
# 权重说明：
#   过关：重持续压力和峰值压力，对手法和节奏中等敏感
#   全连：重失误惩罚和手法复杂度，峰值压力影响大
#   高精度：重判定精度、节奏复杂度和读谱复杂度

DEFAULT_PROFILES: dict[TargetDifficulty, AggregationProfile] = {
    TargetDifficulty.PASS: AggregationProfile(
        target=TargetDifficulty.PASS,
        weights={
            "peak_pressure": 0.20,
            "sustained_pressure": 0.25,
            "technique_complexity": 0.15,
            "rhythm_complexity": 0.10,
            "reading_complexity": 0.10,
            "accuracy_pressure": 0.05,
            "miss_penalty": 0.15,
        },
        peak_boost=0.1,
        description="过关难度：侧重持续输出压力和峰值负担",
    ),
    TargetDifficulty.FULL_COMBO: AggregationProfile(
        target=TargetDifficulty.FULL_COMBO,
        weights={
            "peak_pressure": 0.20,
            "sustained_pressure": 0.10,
            "technique_complexity": 0.20,
            "rhythm_complexity": 0.10,
            "reading_complexity": 0.10,
            "accuracy_pressure": 0.10,
            "miss_penalty": 0.20,
        },
        peak_boost=0.15,
        description="全连难度：侧重失误惩罚和手法/峰值压力",
    ),
    TargetDifficulty.HIGH_ACCURACY: AggregationProfile(
        target=TargetDifficulty.HIGH_ACCURACY,
        weights={
            "peak_pressure": 0.10,
            "sustained_pressure": 0.10,
            "technique_complexity": 0.10,
            "rhythm_complexity": 0.20,
            "reading_complexity": 0.15,
            "accuracy_pressure": 0.25,
            "miss_penalty": 0.10,
        },
        peak_boost=0.1,
        description="高精度难度：侧重判定精度和节奏/读谱复杂度",
    ),
}


def aggregate_target_difficulty(
    dimensions: list[DimensionScore],
    profiles: dict[TargetDifficulty, AggregationProfile] | None = None,
) -> dict[TargetDifficulty, float]:
    """根据维度分数和聚合配置，计算三类目标难度。

    Returns:
        {TargetDifficulty: 分数 (0‑10)}
    """
    profiles = profiles or DEFAULT_PROFILES
    dim_map = {d.name: d.normalized for d in dimensions}

    result: dict[TargetDifficulty, float] = {}

    for target, profile in profiles.items():
        weighted_sum = 0.0
        total_weight = 0.0
        max_contribution = 0.0

        for dim_name, weight in profile.weights.items():
            score = dim_map.get(dim_name, 0.0)
            contribution = score * weight
            weighted_sum += contribution
            total_weight += weight
            max_contribution = max(max_contribution, contribution)

        if total_weight > 0:
            base = weighted_sum / total_weight
        else:
            base = 0.0

        # 峰值加成：如果某维度贡献特别突出，额外提升
        if profile.peak_boost > 0 and total_weight > 0:
            peak_extra = max_contribution / total_weight * profile.peak_boost * 10.0
            base += peak_extra

        result[target] = max(0.0, min(10.0, base))

    return result


def get_aggregation_explanation(
    dimensions: list[DimensionScore],
    profiles: dict[TargetDifficulty, AggregationProfile] | None = None,
) -> dict[TargetDifficulty, str]:
    """返回每种目标难度的聚合说明。"""
    profiles = profiles or DEFAULT_PROFILES
    dim_map = {d.name: d for d in dimensions}

    explanations: dict[TargetDifficulty, str] = {}
    for target, profile in profiles.items():
        parts: list[str] = [profile.description]
        # 找出权重最高的两个维度
        sorted_dims = sorted(profile.weights.items(), key=lambda x: -x[1])[:2]
        for dim_name, weight in sorted_dims:
            d = dim_map.get(dim_name)
            if d:
                parts.append(f"  {d.name}: {d.normalized:.2f} (权重 {weight:.0%})")
        explanations[target] = "\n".join(parts)

    return explanations
