"""可解释性输出生成。

基于计算结果生成难点窗口、文字解释等可解释信息。
"""

from __future__ import annotations

from ..models.result import (
    WindowMetrics, DimensionScore, Hotspot, BranchResult,
)
from ..models.enums import TargetDifficulty

# 维度 → 与哪些目标难度关联最紧密
_DIM_TARGET_MAP: dict[str, list[TargetDifficulty]] = {
    "peak_pressure": [TargetDifficulty.PASS, TargetDifficulty.FULL_COMBO],
    "sustained_pressure": [TargetDifficulty.PASS],
    "technique_complexity": [TargetDifficulty.FULL_COMBO],
    "rhythm_complexity": [TargetDifficulty.HIGH_ACCURACY],
    "reading_complexity": [TargetDifficulty.HIGH_ACCURACY],
    "accuracy_pressure": [TargetDifficulty.HIGH_ACCURACY],
    "miss_penalty": [TargetDifficulty.FULL_COMBO, TargetDifficulty.PASS],
    # 窗口指标名映射
    "instant_pressure": [TargetDifficulty.PASS, TargetDifficulty.FULL_COMBO],
    "recovery_difficulty": [TargetDifficulty.FULL_COMBO, TargetDifficulty.PASS],
}

# 维度 → 解释模板
_EXPLAIN_TEMPLATES: dict[str, str] = {
    "peak_pressure": "存在高密度打击段落，瞬时输出压力较大",
    "sustained_pressure": "持续高密度输出，长时间高打击负担",
    "technique_complexity": "存在复杂配手结构（交替/切换/同手连打）",
    "rhythm_complexity": "节奏模式复杂，拍感偏移或间隔变化频繁",
    "reading_complexity": "变速/变拍/颜色切换密集，视觉识谱负担高",
    "accuracy_pressure": "小间隔密集且节奏不规则，精确判定困难",
    "miss_penalty": "高风险点密集，失误后恢复空间不足",
    # 窗口指标名映射
    "instant_pressure": "瞬时打击密度极高，局部输出压力大",
    "recovery_difficulty": "难点之间恢复空间不足，容易连锁失误",
}


def generate_hotspots(
    window_metrics: list[WindowMetrics],
    dimensions: list[DimensionScore],
    top_n: int = 5,
) -> list[Hotspot]:
    """从滑窗结果中提取最难的若干窗口。"""
    if not window_metrics:
        return []

    # 对每个窗口计算综合难度分
    scored: list[tuple[float, WindowMetrics]] = []
    for wm in window_metrics:
        vals = wm.to_dict()
        total = sum(vals.values())
        scored.append((total, wm))

    scored.sort(key=lambda x: -x[0])

    # 去重（合并重叠窗口）
    hotspots: list[Hotspot] = []
    used_ranges: list[tuple[float, float]] = []

    for score, wm in scored:
        if len(hotspots) >= top_n:
            break
        # 检查是否与已选窗口重叠过多
        overlap = False
        for s, e in used_ranges:
            overlap_start = max(wm.start_time, s)
            overlap_end = min(wm.end_time, e)
            if overlap_end > overlap_start:
                overlap_len = overlap_end - overlap_start
                win_len = wm.end_time - wm.start_time
                if win_len > 0 and overlap_len / win_len > 0.5:
                    overlap = True
                    break
        if overlap:
            continue

        # 找出主要贡献维度
        vals = wm.to_dict()
        sorted_dims = sorted(vals.items(), key=lambda x: -x[1])
        primary = [name for name, v in sorted_dims[:2] if v > 0]

        # 受影响的目标难度
        affected: set[TargetDifficulty] = set()
        for dim_name in primary:
            affected.update(_DIM_TARGET_MAP.get(dim_name, []))

        # 生成解释
        explain_parts = [_EXPLAIN_TEMPLATES.get(d, d) for d in primary]
        explanation = "；".join(explain_parts)

        max_possible = max(score, 1.0)
        severity = min(score / 50.0, 1.0)  # 粗略归一化

        hotspots.append(Hotspot(
            start_time=wm.start_time,
            end_time=wm.end_time,
            severity=severity,
            primary_dimensions=primary,
            affected_targets=sorted(affected, key=lambda t: t.value),
            explanation=explanation,
        ))
        used_ranges.append((wm.start_time, wm.end_time))

    return hotspots


def generate_summary(
    result: BranchResult,
) -> str:
    """生成谱面评定的简要文字总结。"""
    parts: list[str] = []

    # 整体难度
    td = result.target_difficulties
    pass_d = td.get(TargetDifficulty.PASS, 0)
    fc_d = td.get(TargetDifficulty.FULL_COMBO, 0)
    acc_d = td.get(TargetDifficulty.HIGH_ACCURACY, 0)
    parts.append(
        f"综合评定 — 过关: {pass_d:.2f}, 全连: {fc_d:.2f}, 高精度: {acc_d:.2f}"
    )

    # 最突出维度
    if result.dimensions:
        top_dim = max(result.dimensions, key=lambda d: d.normalized)
        parts.append(f"最突出维度: {top_dim.name} ({top_dim.normalized:.2f}/10)")

    # 难点概要
    if result.hotspots:
        h = result.hotspots[0]
        parts.append(
            f"最难段落: {h.start_time:.1f}s ~ {h.end_time:.1f}s — {h.explanation}"
        )

    return "\n".join(parts)
