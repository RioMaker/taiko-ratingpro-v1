"""维度3：手法复杂度。

定义：配手、换手、交替、同手连续、高密模式等造成的操作复杂性。
第一版使用简化配手推断（规则版），接口允许后续升级为 DP 模型。
"""

from __future__ import annotations

import numpy as np

from .base import BaseDimension
from ..features.note_features import NoteFeature
from ..models.result import WindowMetrics, DimensionScore


class TechniqueComplexity(BaseDimension):
    name = "technique_complexity"
    display_name = "手法复杂度"

    def compute(
        self,
        features: list[NoteFeature],
        window_metrics: list[WindowMetrics],
    ) -> DimensionScore:
        if not features or len(features) < 2:
            return DimensionScore(name=self.name, raw_value=0.0, normalized=0.0)

        n = len(features)

        # --- 颜色切换分析 ---
        switches = sum(1 for f in features if f.color_switch)
        switch_ratio = switches / (n - 1)

        # --- 连续同色分析 ---
        # 连续同色后突然切换 → 配手压力
        runs = _color_runs(features)
        # 长同色串后的切换越多越难
        hard_transitions = sum(1 for r in runs if r >= 4)
        hard_trans_ratio = hard_transitions / max(len(runs), 1)

        # --- 高密度下的切换 ---
        # 高速率区间内的颜色切换更难
        fast_switch_count = sum(
            1 for f in features
            if f.color_switch and f.instant_rate > 10.0
        )
        fast_switch_ratio = fast_switch_count / max(n, 1)

        # --- 交替模式检测 ---
        # 检测 dkdk 或 kdkd 交替串
        alternating_runs = _alternating_run_lengths(features)
        max_alt = max(alternating_runs) if alternating_runs else 0
        alt_score = min(max_alt / 16.0, 1.0)  # 16连交替为满分

        # --- 简化配手代价估算 ---
        # 假设交替模式最简单（自然交替手），同色连续需要同手连打
        # 代价 = 高速同色连打长度 + 快速交替中的突变
        rapid_same_hand = 0
        for i in range(1, n):
            if not features[i].color_switch and features[i].instant_rate > 12.0:
                rapid_same_hand += 1
        same_hand_ratio = rapid_same_hand / max(n, 1)

        # 窗口级技术复杂度
        technique_metrics = [
            wm.technique_complexity for wm in window_metrics if wm.window_size == "short"
        ]
        peak_technique = max(technique_metrics) if technique_metrics else 0.0

        # 综合原始值
        raw = (
            switch_ratio * 2.5
            + hard_trans_ratio * 2.0
            + fast_switch_ratio * 2.0
            + alt_score * 1.0
            + same_hand_ratio * 1.5
            + min(peak_technique * 0.3, 1.0)
        )

        normalized = self._normalize(raw)

        return DimensionScore(
            name=self.name,
            raw_value=raw,
            normalized=normalized,
            details={
                "switch_ratio": round(switch_ratio, 4),
                "hard_transitions": hard_transitions,
                "fast_switch_ratio": round(fast_switch_ratio, 4),
                "max_alternating_run": max_alt,
                "same_hand_pressure": round(same_hand_ratio, 4),
            },
        )


def _color_runs(features: list[NoteFeature]) -> list[int]:
    """连续同色音符的游程长度列表。"""
    if not features:
        return []
    runs = []
    cur = 1
    for i in range(1, len(features)):
        if features[i].color == features[i - 1].color:
            cur += 1
        else:
            runs.append(cur)
            cur = 1
    runs.append(cur)
    return runs


def _alternating_run_lengths(features: list[NoteFeature]) -> list[int]:
    """交替颜色（dkdk...）的最长连续长度列表。"""
    if len(features) < 2:
        return [0]
    runs = []
    cur = 1
    for i in range(1, len(features)):
        if features[i].color_switch:
            cur += 1
        else:
            runs.append(cur)
            cur = 1
    runs.append(cur)
    return runs
