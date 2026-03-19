"""维度1：峰值输出压力。

定义：短时间窗口内的最高局部打击负担。
使用高分位数的局部速率特征，突出局部高压点。
"""

from __future__ import annotations

import numpy as np

from .base import BaseDimension
from ..features.note_features import NoteFeature
from ..models.result import WindowMetrics, DimensionScore


class PeakPressure(BaseDimension):
    name = "peak_pressure"
    display_name = "峰值输出压力"

    # 标准化参数（可外部配置）
    RATE_CEILING = 25.0  # 速率天花板（打/秒），超过此值视为满分

    def compute(
        self,
        features: list[NoteFeature],
        window_metrics: list[WindowMetrics],
    ) -> DimensionScore:
        if not features:
            return DimensionScore(name=self.name, raw_value=0.0, normalized=0.0)

        rates = np.array([f.instant_rate for f in features])
        w4_rates = np.array([f.window4_rate for f in features])

        # 取 P95 瞬时速率
        p95_instant = float(np.percentile(rates, 95)) if len(rates) > 0 else 0.0
        # 取 P90 四音符窗口速率
        p90_w4 = float(np.percentile(w4_rates, 90)) if len(w4_rates) > 0 else 0.0

        # 短窗口的峰值压力
        short_pressures = [
            wm.instant_pressure for wm in window_metrics if wm.window_size == "short"
        ]
        peak_window = max(short_pressures) if short_pressures else 0.0

        # 综合：加权混合
        raw = 0.4 * p95_instant + 0.3 * p90_w4 + 0.3 * peak_window
        normalized = self._normalize(raw, scale=10.0 / self.RATE_CEILING)

        return DimensionScore(
            name=self.name,
            raw_value=raw,
            normalized=normalized,
            details={
                "p95_instant_rate": round(p95_instant, 3),
                "p90_window4_rate": round(p90_w4, 3),
                "peak_short_window": round(peak_window, 3),
            },
        )
