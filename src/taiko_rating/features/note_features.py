"""音符级特征提取。

从标准化谱面中为每个击打音符计算局部特征向量。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from ..models.chart import Note, ChartBranch
from ..models.enums import NoteType


@dataclass
class NoteFeature:
    """单个音符的特征集合。"""
    index: int
    time: float
    note_type: NoteType
    # 时间间隔
    interval: float              # 与上一个击打音符的间隔（秒）
    # 速率
    instant_rate: float          # 1 / interval（打击/秒）
    window2_rate: float          # 2音符窗口平均速率
    window4_rate: float          # 4音符窗口平均速率
    window8_rate: float          # 8音符窗口平均速率
    # 颜色 / 手法
    color: str | None            # "don" / "ka" / None
    color_switch: bool           # 是否与上一个音符颜色不同
    is_big: bool
    # 节奏
    beat_pos: float
    bpm: float
    bpm_change: float            # 与上一个音符的 BPM 变化量
    # 视觉
    scroll: float
    scroll_change: float         # 与上一个音符的 scroll 变化量
    # 小节
    measure_num: int
    measure_boundary: bool       # 是否跨小节
    time_signature: tuple[int, int]
    # 分支
    is_branch_start: bool
    # 额外
    meta: dict[str, Any] = field(default_factory=dict)


def extract_note_features(branch: ChartBranch) -> list[NoteFeature]:
    """从分支中提取全部击打音符的特征列表。"""
    hits = branch.hit_notes
    if not hits:
        return []

    features: list[NoteFeature] = []
    for idx, note in enumerate(hits):
        prev = hits[idx - 1] if idx > 0 else None
        interval = (note.time - prev.time) if prev else float("inf")
        if interval <= 0:
            interval = 1e-6  # 避免除零

        instant_rate = 1.0 / interval if interval < float("inf") else 0.0
        w2_rate = _window_rate(hits, idx, 2)
        w4_rate = _window_rate(hits, idx, 4)
        w8_rate = _window_rate(hits, idx, 8)

        color = note.note_type.color
        prev_color = prev.note_type.color if prev else None
        color_switch = (color is not None and prev_color is not None
                        and color != prev_color)

        bpm_change = (note.bpm - prev.bpm) if prev else 0.0
        scroll_change = (note.scroll - prev.scroll) if prev else 0.0
        measure_boundary = (prev is not None and note.measure_num != prev.measure_num)

        features.append(NoteFeature(
            index=idx,
            time=note.time,
            note_type=note.note_type,
            interval=interval,
            instant_rate=instant_rate,
            window2_rate=w2_rate,
            window4_rate=w4_rate,
            window8_rate=w8_rate,
            color=color,
            color_switch=color_switch,
            is_big=note.note_type.is_big,
            beat_pos=note.beat_pos,
            bpm=note.bpm,
            bpm_change=bpm_change,
            scroll=note.scroll,
            scroll_change=scroll_change,
            measure_num=note.measure_num,
            measure_boundary=measure_boundary,
            time_signature=note.time_signature,
            is_branch_start=note.is_branch_start,
        ))

    return features


def _window_rate(hits: list[Note], idx: int, window: int) -> float:
    """计算以 idx 结尾的 window 个音符的平均速率。"""
    if idx < window - 1:
        return 0.0
    start = hits[idx - window + 1]
    end = hits[idx]
    dt = end.time - start.time
    if dt <= 0:
        return 0.0
    return (window - 1) / dt


def features_to_arrays(features: list[NoteFeature]) -> dict[str, np.ndarray]:
    """将特征列表转为 numpy 数组字典，便于后续向量化计算。"""
    if not features:
        return {}
    return {
        "time": np.array([f.time for f in features]),
        "interval": np.array([f.interval for f in features]),
        "instant_rate": np.array([f.instant_rate for f in features]),
        "window2_rate": np.array([f.window2_rate for f in features]),
        "window4_rate": np.array([f.window4_rate for f in features]),
        "window8_rate": np.array([f.window8_rate for f in features]),
        "color_switch": np.array([1.0 if f.color_switch else 0.0 for f in features]),
        "is_big": np.array([1.0 if f.is_big else 0.0 for f in features]),
        "beat_pos": np.array([f.beat_pos for f in features]),
        "bpm": np.array([f.bpm for f in features]),
        "bpm_change": np.array([abs(f.bpm_change) for f in features]),
        "scroll": np.array([f.scroll for f in features]),
        "scroll_change": np.array([abs(f.scroll_change) for f in features]),
    }
