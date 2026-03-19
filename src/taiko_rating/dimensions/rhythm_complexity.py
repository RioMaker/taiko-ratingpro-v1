"""维度4：节奏复杂度。

定义：节奏比例变化、切分、拍感偏移、模式难预测性造成的理解压力。
考虑节奏模式本身，而不只看 BPM。
"""

from __future__ import annotations

import math
import numpy as np

from .base import BaseDimension
from ..features.note_features import NoteFeature
from ..models.result import WindowMetrics, DimensionScore


class RhythmComplexity(BaseDimension):
    name = "rhythm_complexity"
    display_name = "节奏复杂度"

    def compute(
        self,
        features: list[NoteFeature],
        window_metrics: list[WindowMetrics],
    ) -> DimensionScore:
        if not features or len(features) < 3:
            return DimensionScore(name=self.name, raw_value=0.0, normalized=0.0)

        intervals = np.array([f.interval for f in features])
        # 排除无穷大（第一个音符）
        valid_mask = intervals < 100.0
        valid_intervals = intervals[valid_mask]

        if len(valid_intervals) < 3:
            return DimensionScore(name=self.name, raw_value=0.0, normalized=0.0)

        # 1. 间隔比例复杂度（rhythmic surprisal）
        ratios = valid_intervals[1:] / np.maximum(valid_intervals[:-1], 1e-6)
        log_ratios = np.log2(np.clip(ratios, 0.1, 10.0))
        ratio_std = float(np.std(log_ratios))
        # 偏离简单整数比的程度
        simple_ratios = np.array([1.0, 0.5, 2.0, 0.25, 4.0, 1.5, 0.75, 3.0])
        departures = []
        for r in ratios:
            min_dist = min(abs(r - sr) for sr in simple_ratios)
            departures.append(min_dist)
        departure_mean = float(np.mean(departures))

        # 2. 拍位分布复杂度
        beat_positions = np.array([f.beat_pos for f in features])
        # 量化拍位到 16 分位
        quantized = np.round(beat_positions * 16) / 16
        unique_positions = len(np.unique(quantized))
        beat_entropy = _entropy_discrete(quantized)

        # 3. 模式突变检测
        # 用短窗口检测间隔模式变化
        pattern_changes = 0
        window = 4
        for i in range(window, len(valid_intervals)):
            prev_pattern = valid_intervals[i - window:i]
            curr = valid_intervals[i]
            predicted = float(np.mean(prev_pattern))
            if predicted > 0 and abs(curr - predicted) / predicted > 0.4:
                pattern_changes += 1
        change_ratio = pattern_changes / max(len(valid_intervals) - window, 1)

        # 4. 节奏可预测性（用自相关评估）
        if len(valid_intervals) > 8:
            autocorr = _autocorrelation(valid_intervals, lag=4)
            predictability = max(0.0, autocorr)
            unpredictability = 1.0 - predictability
        else:
            unpredictability = 0.5

        # 窗口级节奏复杂度
        rhythm_metrics = [
            wm.rhythm_complexity for wm in window_metrics if wm.window_size == "medium"
        ]
        mean_window_rhythm = float(np.mean(rhythm_metrics)) if rhythm_metrics else 0.0

        # 综合
        raw = (
            ratio_std * 2.0
            + departure_mean * 2.0
            + beat_entropy * 0.8
            + change_ratio * 3.0
            + unpredictability * 1.0
            + min(mean_window_rhythm * 0.3, 1.2)
        )

        normalized = self._normalize(raw)

        return DimensionScore(
            name=self.name,
            raw_value=raw,
            normalized=normalized,
            details={
                "ratio_std": round(ratio_std, 4),
                "departure_from_simple": round(departure_mean, 4),
                "beat_entropy": round(beat_entropy, 4),
                "pattern_change_ratio": round(change_ratio, 4),
                "unpredictability": round(unpredictability, 4),
                "unique_beat_positions": unique_positions,
            },
        )


def _entropy_discrete(arr: np.ndarray) -> float:
    """离散值的信息熵。"""
    _, counts = np.unique(arr, return_counts=True)
    probs = counts / counts.sum()
    return -float(np.sum(probs * np.log2(probs + 1e-12)))


def _autocorrelation(arr: np.ndarray, lag: int) -> float:
    """计算给定延迟的自相关系数。"""
    n = len(arr)
    if n <= lag:
        return 0.0
    mean = np.mean(arr)
    var = np.var(arr)
    if var < 1e-12:
        return 1.0
    shifted = arr[lag:] - mean
    original = arr[:n - lag] - mean
    return float(np.sum(shifted * original) / ((n - lag) * var))
