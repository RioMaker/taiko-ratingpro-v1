"""聚合与目标难度测试。"""

import pytest
from taiko_rating.aggregation.target_difficulty import (
    aggregate_target_difficulty,
    get_aggregation_explanation,
    DEFAULT_PROFILES,
)
from taiko_rating.models.result import DimensionScore
from taiko_rating.models.enums import TargetDifficulty


def _make_dim_scores(values: dict[str, float]) -> list[DimensionScore]:
    return [DimensionScore(name=k, raw_value=v, normalized=v) for k, v in values.items()]


class TestAggregation:
    def test_returns_three_targets(self):
        dims = _make_dim_scores({
            "peak_pressure": 5.0,
            "sustained_pressure": 5.0,
            "technique_complexity": 5.0,
            "rhythm_complexity": 5.0,
            "reading_complexity": 5.0,
            "accuracy_pressure": 5.0,
            "miss_penalty": 5.0,
        })
        result = aggregate_target_difficulty(dims)
        assert TargetDifficulty.PASS in result
        assert TargetDifficulty.FULL_COMBO in result
        assert TargetDifficulty.HIGH_ACCURACY in result

    def test_scores_in_range(self):
        dims = _make_dim_scores({
            "peak_pressure": 8.0,
            "sustained_pressure": 3.0,
            "technique_complexity": 6.0,
            "rhythm_complexity": 7.0,
            "reading_complexity": 4.0,
            "accuracy_pressure": 9.0,
            "miss_penalty": 5.0,
        })
        result = aggregate_target_difficulty(dims)
        for v in result.values():
            assert 0 <= v <= 10

    def test_different_weights_different_scores(self):
        # 高精度压力高，其他低 → 高精度难度应偏高
        dims = _make_dim_scores({
            "peak_pressure": 1.0,
            "sustained_pressure": 1.0,
            "technique_complexity": 1.0,
            "rhythm_complexity": 1.0,
            "reading_complexity": 1.0,
            "accuracy_pressure": 9.0,
            "miss_penalty": 1.0,
        })
        result = aggregate_target_difficulty(dims)
        assert result[TargetDifficulty.HIGH_ACCURACY] > result[TargetDifficulty.PASS]

    def test_all_zero(self):
        dims = _make_dim_scores({
            "peak_pressure": 0.0,
            "sustained_pressure": 0.0,
            "technique_complexity": 0.0,
            "rhythm_complexity": 0.0,
            "reading_complexity": 0.0,
            "accuracy_pressure": 0.0,
            "miss_penalty": 0.0,
        })
        result = aggregate_target_difficulty(dims)
        for v in result.values():
            assert v == 0.0

    def test_explanation(self):
        dims = _make_dim_scores({
            "peak_pressure": 5.0,
            "sustained_pressure": 5.0,
            "technique_complexity": 5.0,
            "rhythm_complexity": 5.0,
            "reading_complexity": 5.0,
            "accuracy_pressure": 5.0,
            "miss_penalty": 5.0,
        })
        explanations = get_aggregation_explanation(dims)
        assert TargetDifficulty.PASS in explanations
        assert len(explanations[TargetDifficulty.PASS]) > 0
