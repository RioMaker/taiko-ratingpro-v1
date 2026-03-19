"""维度5：读谱复杂度。

定义：视觉密度、颜色分组、变速、拍号变化等造成的识谱负担。
第一版使用代理特征实现。
"""

from __future__ import annotations

import numpy as np

from .base import BaseDimension
from ..features.note_features import NoteFeature
from ..models.result import WindowMetrics, DimensionScore


class ReadingComplexity(BaseDimension):
    name = "reading_complexity"
    display_name = "读谱复杂度"

    def compute(
        self,
        features: list[NoteFeature],
        window_metrics: list[WindowMetrics],
    ) -> DimensionScore:
        if not features or len(features) < 2:
            return DimensionScore(name=self.name, raw_value=0.0, normalized=0.0)

        n = len(features)
        times = np.array([f.time for f in features])
        total_duration = times[-1] - times[0]
        if total_duration <= 0:
            total_duration = 1.0

        # 1. BPM 变化次数与幅度
        bpm_changes = sum(1 for f in features if abs(f.bpm_change) > 0.5)
        bpm_magnitudes = [abs(f.bpm_change) for f in features if abs(f.bpm_change) > 0.5]
        bpm_change_score = min(bpm_changes / max(n, 1) * 10.0, 3.0)
        bpm_magnitude_score = min(
            (sum(bpm_magnitudes) / max(len(bpm_magnitudes), 1)) / 50.0 * 3.0, 3.0
        ) if bpm_magnitudes else 0.0

        # 2. HS 变化次数与幅度
        scroll_changes = sum(1 for f in features if abs(f.scroll_change) > 0.01)
        scroll_magnitudes = [abs(f.scroll_change) for f in features if abs(f.scroll_change) > 0.01]
        scroll_change_score = min(scroll_changes / max(n, 1) * 10.0, 3.0)
        scroll_mag_score = min(
            (sum(scroll_magnitudes) / max(len(scroll_magnitudes), 1)) / 2.0 * 2.0, 2.0
        ) if scroll_magnitudes else 0.0

        # 3. 颜色切换密度
        color_switches = sum(1 for f in features if f.color_switch)
        switch_density = color_switches / total_duration  # 次/秒
        switch_score = min(switch_density / 5.0 * 2.0, 2.0)

        # 4. 拍号变化
        time_sigs = set()
        for f in features:
            time_sigs.add(f.time_signature)
        sig_variety = len(time_sigs) - 1  # 减去基本拍号
        sig_score = min(sig_variety * 1.0, 2.0)

        # 5. 视觉高压段密度（高密度 + 变速叠加）
        visual_pressure_count = 0
        for f in features:
            if f.instant_rate > 12.0 and (abs(f.scroll_change) > 0.01 or abs(f.bpm_change) > 1.0):
                visual_pressure_count += 1
        visual_score = min(visual_pressure_count / max(n, 1) * 10.0, 2.0)

        # 窗口级读谱复杂度
        reading_metrics = [
            wm.reading_complexity for wm in window_metrics if wm.window_size == "medium"
        ]
        mean_window = float(np.mean(reading_metrics)) if reading_metrics else 0.0

        raw = (
            bpm_change_score
            + bpm_magnitude_score
            + scroll_change_score
            + scroll_mag_score
            + switch_score
            + sig_score
            + visual_score
            + min(mean_window * 0.2, 1.0)
        )

        normalized = self._normalize(raw)

        return DimensionScore(
            name=self.name,
            raw_value=raw,
            normalized=normalized,
            details={
                "bpm_change_count": bpm_changes,
                "scroll_change_count": scroll_changes,
                "color_switch_density": round(switch_density, 3),
                "time_signature_variety": sig_variety + 1,
                "visual_pressure_notes": visual_pressure_count,
            },
        )
