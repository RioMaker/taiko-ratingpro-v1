"""段落级滑窗分析。

对音符特征序列进行多尺度滑动时间窗口分析，输出每个窗口的局部指标。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence
import math

import numpy as np

from ..features.note_features import NoteFeature
from ..models.result import WindowMetrics


# 三种窗口尺度（秒）
WINDOW_CONFIGS = {
    "short": (2.0, 3.0),    # 2‑3 秒
    "medium": (5.0, 8.0),   # 5‑8 秒
    "long": (12.0, 20.0),   # 12‑20 秒
}

# 每种尺度使用的具体窗口大小
DEFAULT_WINDOWS = {
    "short": 2.5,
    "medium": 6.0,
    "long": 15.0,
}

# 窗口滑动步长（秒）
STEP_RATIO = 0.25  # 窗口大小的 25%


def sliding_window_analysis(
    features: list[NoteFeature],
    window_sizes: dict[str, float] | None = None,
) -> list[WindowMetrics]:
    """对特征序列执行多尺度滑窗分析。

    返回所有窗口的指标列表。
    """
    if not features or len(features) < 2:
        return []

    sizes = window_sizes or DEFAULT_WINDOWS
    times = np.array([f.time for f in features])
    start_t = times[0]
    end_t = times[-1]

    all_metrics: list[WindowMetrics] = []

    for label, win_size in sizes.items():
        step = win_size * STEP_RATIO
        t = start_t
        while t + win_size <= end_t + step:
            w_end = t + win_size
            mask = (times >= t) & (times < w_end)
            window_feats = [f for f, m in zip(features, mask) if m]

            if len(window_feats) >= 2:
                wm = _compute_window_metrics(window_feats, t, w_end, label)
                all_metrics.append(wm)
            t += step

    return all_metrics


def _compute_window_metrics(
    feats: list[NoteFeature],
    start: float, end: float, label: str,
) -> WindowMetrics:
    """计算单个窗口的七项指标。"""
    n = len(feats)
    duration = end - start
    if duration <= 0:
        duration = 1e-6

    intervals = np.array([f.interval for f in feats])
    rates = np.array([f.instant_rate for f in feats])
    color_switches = np.array([1.0 if f.color_switch else 0.0 for f in feats])
    bpm_changes = np.array([abs(f.bpm_change) for f in feats])
    scroll_changes = np.array([abs(f.scroll_change) for f in feats])
    beat_positions = np.array([f.beat_pos for f in feats])

    # 1. 瞬时输出压力：窗口内最高速率的高分位数
    instant_pressure = float(np.percentile(rates, 90)) if n > 0 else 0.0

    # 2. 连续输出压力：窗口内平均速率 × 密度系数
    density = n / duration
    mean_rate = float(np.mean(rates))
    sustained_pressure = mean_rate * min(density / 10.0, 2.0)

    # 3. 手法复杂度：颜色切换比率 + 连续同色序列分析
    switch_ratio = float(np.mean(color_switches)) if n > 1 else 0.0
    # 计算连续同色长度的方差作为配手困难度指标
    same_runs = _run_lengths(feats)
    run_variance = float(np.var(same_runs)) if len(same_runs) > 1 else 0.0
    technique = switch_ratio * 5.0 + min(run_variance, 5.0)

    # 4. 节奏复杂度：间隔比例变化 + 拍位分散度
    if n > 2:
        valid_intervals = intervals[intervals < float("inf")]
        if len(valid_intervals) > 2:
            ratios = valid_intervals[1:] / np.maximum(valid_intervals[:-1], 1e-6)
            ratio_complexity = float(np.std(np.log2(np.clip(ratios, 0.1, 10.0))))
        else:
            ratio_complexity = 0.0
        beat_spread = float(np.std(beat_positions))
        rhythm = ratio_complexity * 3.0 + beat_spread * 2.0
    else:
        rhythm = 0.0

    # 5. 读谱复杂度：BPM变化 + scroll变化 + 颜色切换密度
    bpm_factor = float(np.sum(bpm_changes > 0)) / max(n, 1) * 5.0
    scroll_factor = float(np.sum(scroll_changes > 0)) / max(n, 1) * 5.0
    color_density = switch_ratio * density
    reading = bpm_factor + scroll_factor + min(color_density, 5.0)

    # 6. 判定精度压力：小间隔比例 × 速率方差
    small_interval_ratio = float(np.mean(intervals < 0.1)) if n > 0 else 0.0
    rate_var = float(np.std(rates)) if n > 1 else 0.0
    accuracy = small_interval_ratio * 5.0 + min(rate_var * 0.5, 5.0)

    # 7. 恢复难度：高速段占比 + 无间歇长度
    high_rate_threshold = max(float(np.median(rates)) * 1.5, 5.0)
    high_rate_ratio = float(np.mean(rates > high_rate_threshold)) if n > 0 else 0.0
    max_consecutive_high = _max_consecutive(rates > high_rate_threshold)
    recovery = high_rate_ratio * 5.0 + min(max_consecutive_high / max(n, 1) * 5.0, 5.0)

    return WindowMetrics(
        start_time=start,
        end_time=end,
        window_size=label,
        instant_pressure=instant_pressure,
        sustained_pressure=sustained_pressure,
        technique_complexity=technique,
        rhythm_complexity=rhythm,
        reading_complexity=reading,
        accuracy_pressure=accuracy,
        recovery_difficulty=recovery,
    )


def _run_lengths(feats: list[NoteFeature]) -> list[int]:
    """计算连续同色音符的游程长度列表。"""
    if not feats:
        return []
    runs = []
    current_run = 1
    for i in range(1, len(feats)):
        if feats[i].color == feats[i - 1].color:
            current_run += 1
        else:
            runs.append(current_run)
            current_run = 1
    runs.append(current_run)
    return runs


def _max_consecutive(mask: np.ndarray) -> int:
    """计算布尔数组中最长连续 True 序列长度。"""
    if len(mask) == 0:
        return 0
    max_run = 0
    current = 0
    for v in mask:
        if v:
            current += 1
            max_run = max(max_run, current)
        else:
            current = 0
    return max_run
