"""维度6：判定精度压力。

定义：为了获得高精度判定所需的时间控制难度。
与高密度、快慢变化、节奏复杂性联动，但不等同于高速。
"""

from __future__ import annotations

import numpy as np

from .base import BaseDimension
from ..features.note_features import NoteFeature
from ..models.result import WindowMetrics, DimensionScore


class AccuracyPressure(BaseDimension):
    name = "accuracy_pressure"
    display_name = "判定精度压力"

    # 判定窗口参考（秒，太鼓达人「良」判定约 ±25ms）
    GOOD_WINDOW = 0.025

    def compute(
        self,
        features: list[NoteFeature],
        window_metrics: list[WindowMetrics],
    ) -> DimensionScore:
        if not features or len(features) < 2:
            return DimensionScore(name=self.name, raw_value=0.0, normalized=0.0)

        n = len(features)
        intervals = np.array([f.interval for f in features])
        valid_mask = intervals < 100.0
        valid_intervals = intervals[valid_mask]

        if len(valid_intervals) < 2:
            return DimensionScore(name=self.name, raw_value=0.0, normalized=0.0)

        # 1. 小间隔分布：间隔 < 100ms 的比例
        tiny_ratio = float(np.mean(valid_intervals < 0.1))
        small_ratio = float(np.mean(valid_intervals < 0.15))

        # 2. 高速区间内的节奏复杂性
        fast_features = [f for f in features if f.instant_rate > 10.0]
        if len(fast_features) > 2:
            fast_intervals = np.array([f.interval for f in fast_features if f.interval < 100])
            if len(fast_intervals) > 2:
                fast_rhythm_var = float(np.std(fast_intervals) / np.mean(fast_intervals))
            else:
                fast_rhythm_var = 0.0
        else:
            fast_rhythm_var = 0.0

        # 3. 变速后的局部控制要求
        speed_change_zones = 0
        for i in range(1, n):
            if abs(features[i].bpm_change) > 5.0 or abs(features[i].scroll_change) > 0.2:
                # 变速后 4 个音符内的间隔方差
                end = min(i + 4, n)
                zone_intervals = [features[j].interval for j in range(i, end)
                                  if features[j].interval < 100]
                if len(zone_intervals) >= 2:
                    zone_var = float(np.std(zone_intervals))
                    if zone_var > 0.02:
                        speed_change_zones += 1
        speed_change_score = min(speed_change_zones / max(n, 1) * 20.0, 3.0)

        # 4. 整体间隔紧密度
        median_interval = float(np.median(valid_intervals))
        tightness = max(0.0, 1.0 - median_interval / 0.2) * 3.0  # 越短越紧

        # 窗口级精度压力
        acc_metrics = [
            wm.accuracy_pressure for wm in window_metrics if wm.window_size == "short"
        ]
        peak_acc = max(acc_metrics) if acc_metrics else 0.0

        raw = (
            tiny_ratio * 3.0
            + small_ratio * 1.5
            + fast_rhythm_var * 2.0
            + speed_change_score
            + min(tightness, 3.0)
            + min(peak_acc * 0.3, 1.0)
        )

        normalized = self._normalize(raw)

        return DimensionScore(
            name=self.name,
            raw_value=raw,
            normalized=normalized,
            details={
                "tiny_interval_ratio": round(tiny_ratio, 4),
                "small_interval_ratio": round(small_ratio, 4),
                "fast_rhythm_variance": round(fast_rhythm_var, 4),
                "speed_change_zones": speed_change_zones,
                "median_interval_ms": round(median_interval * 1000, 1),
            },
        )
