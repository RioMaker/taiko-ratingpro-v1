"""维度2：持续输出压力。

定义：高负担状态持续的时间和面积。
能区分"短爆发"和"长时间高压"。
"""

from __future__ import annotations

import numpy as np

from .base import BaseDimension
from ..features.note_features import NoteFeature
from ..models.result import WindowMetrics, DimensionScore


class SustainedPressure(BaseDimension):
    name = "sustained_pressure"
    display_name = "持续输出压力"

    HIGH_RATE_THRESHOLD = 8.0  # 高压速率阈值（打/秒）
    MAX_SUSTAINED_SCORE = 10.0

    def compute(
        self,
        features: list[NoteFeature],
        window_metrics: list[WindowMetrics],
    ) -> DimensionScore:
        if not features or len(features) < 2:
            return DimensionScore(name=self.name, raw_value=0.0, normalized=0.0)

        rates = np.array([f.instant_rate for f in features])
        times = np.array([f.time for f in features])
        total_duration = times[-1] - times[0]
        if total_duration <= 0:
            return DimensionScore(name=self.name, raw_value=0.0, normalized=0.0)

        # 自适应阈值：取中位速率的 1.5 倍与固定值的较大者
        adaptive_threshold = max(float(np.median(rates)) * 1.5, self.HIGH_RATE_THRESHOLD)

        high_mask = rates >= adaptive_threshold

        # 1. 高压窗口面积（速率超阈值的"面积"）
        high_area = 0.0
        for i in range(len(features)):
            if high_mask[i]:
                dt = features[i].interval if features[i].interval < float("inf") else 0
                high_area += rates[i] * min(dt, 1.0)

        # 2. 最长高压持续时间
        max_high_duration = 0.0
        current_start: float | None = None
        for i in range(len(features)):
            if high_mask[i]:
                if current_start is None:
                    current_start = times[i]
            else:
                if current_start is not None:
                    dur = times[i] - current_start
                    max_high_duration = max(max_high_duration, dur)
                    current_start = None
        if current_start is not None:
            max_high_duration = max(max_high_duration, times[-1] - current_start)

        # 3. 高压占比
        high_ratio = float(np.mean(high_mask))

        # 中窗口持续压力指标
        medium_sustained = [
            wm.sustained_pressure for wm in window_metrics if wm.window_size == "medium"
        ]
        mean_medium = float(np.mean(medium_sustained)) if medium_sustained else 0.0

        # 综合
        raw = (
            0.3 * min(high_area / max(total_duration, 1.0), 20.0)
            + 0.3 * min(max_high_duration / max(total_duration, 1.0) * 10.0, 10.0)
            + 0.2 * high_ratio * 10.0
            + 0.2 * min(mean_medium, 10.0)
        )

        normalized = self._normalize(raw)

        return DimensionScore(
            name=self.name,
            raw_value=raw,
            normalized=normalized,
            details={
                "high_area": round(high_area, 3),
                "max_high_duration": round(max_high_duration, 3),
                "high_ratio": round(high_ratio, 4),
                "adaptive_threshold": round(adaptive_threshold, 3),
            },
        )
