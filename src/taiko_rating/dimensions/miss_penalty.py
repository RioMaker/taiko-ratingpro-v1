"""维度7：失误惩罚强度。

定义：某处失误后是否容易连锁崩坏，以及恢复空间是否充足。
体现难点间距、恢复长度、高风险点聚集程度。
"""

from __future__ import annotations

import numpy as np

from .base import BaseDimension
from ..features.note_features import NoteFeature
from ..models.result import WindowMetrics, DimensionScore


class MissPenalty(BaseDimension):
    name = "miss_penalty"
    display_name = "失误惩罚强度"

    # 高风险速率阈值
    RISK_RATE_THRESHOLD = 10.0

    def compute(
        self,
        features: list[NoteFeature],
        window_metrics: list[WindowMetrics],
    ) -> DimensionScore:
        if not features or len(features) < 2:
            return DimensionScore(name=self.name, raw_value=0.0, normalized=0.0)

        n = len(features)
        times = np.array([f.time for f in features])
        rates = np.array([f.instant_rate for f in features])
        total_duration = times[-1] - times[0]
        if total_duration <= 0:
            return DimensionScore(name=self.name, raw_value=0.0, normalized=0.0)

        # 自适应高风险阈值
        risk_threshold = max(
            float(np.percentile(rates, 75)),
            self.RISK_RATE_THRESHOLD,
        )
        risk_mask = rates >= risk_threshold

        # 1. 高风险点之间的恢复间距
        risk_indices = np.where(risk_mask)[0]
        if len(risk_indices) >= 2:
            risk_times = times[risk_indices]
            gaps = np.diff(risk_times)
            # 恢复间距太小 → 高惩罚
            short_gap_ratio = float(np.mean(gaps < 1.0))
            min_gap = float(np.min(gaps)) if len(gaps) > 0 else float("inf")
        else:
            short_gap_ratio = 0.0
            min_gap = float("inf")

        # 2. 连续危险窗口长度（最长连续高风险段）
        max_danger_run = 0
        current_run = 0
        for r in risk_mask:
            if r:
                current_run += 1
                max_danger_run = max(max_danger_run, current_run)
            else:
                current_run = 0
        danger_run_ratio = max_danger_run / max(n, 1)

        # 3. 恢复区分析（两个高压段之间的低压长度）
        recovery_lengths: list[float] = []
        in_recovery = False
        recovery_start = 0.0
        for i in range(n):
            if risk_mask[i]:
                if in_recovery:
                    recovery_lengths.append(times[i] - recovery_start)
                    in_recovery = False
            else:
                if not in_recovery:
                    recovery_start = times[i]
                    in_recovery = True

        if recovery_lengths:
            mean_recovery = float(np.mean(recovery_lengths))
            short_recovery_ratio = float(np.mean(np.array(recovery_lengths) < 1.5))
        else:
            mean_recovery = total_duration
            short_recovery_ratio = 0.0

        # 4. 局部崩坏传播风险（高密度区内连续高难度）
        cascade_risk = 0.0
        for i in range(n - 3):
            local_risk = sum(1 for j in range(i, min(i + 4, n)) if risk_mask[j])
            if local_risk >= 3:
                cascade_risk += 1
        cascade_ratio = cascade_risk / max(n - 3, 1)

        # 窗口级恢复难度
        recovery_metrics = [
            wm.recovery_difficulty for wm in window_metrics if wm.window_size == "long"
        ]
        mean_window_recovery = float(np.mean(recovery_metrics)) if recovery_metrics else 0.0

        raw = (
            short_gap_ratio * 2.5
            + danger_run_ratio * 2.5
            + short_recovery_ratio * 2.0
            + cascade_ratio * 2.0
            + min(mean_window_recovery * 0.3, 1.0)
        )

        normalized = self._normalize(raw)

        return DimensionScore(
            name=self.name,
            raw_value=raw,
            normalized=normalized,
            details={
                "risk_point_count": int(risk_mask.sum()),
                "short_gap_ratio": round(short_gap_ratio, 4),
                "max_danger_run": max_danger_run,
                "mean_recovery_sec": round(mean_recovery, 3),
                "short_recovery_ratio": round(short_recovery_ratio, 4),
                "cascade_ratio": round(cascade_ratio, 4),
            },
        )
