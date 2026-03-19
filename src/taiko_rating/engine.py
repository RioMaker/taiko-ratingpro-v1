"""评定引擎 — 主计算流程。

四层流水线：
  1. 特征提取层 (features)
  2. 维度计算层 (dimensions)
  3. 聚合层 (aggregation)
  4. 标定层 (normalization) — 第一版内嵌规则标准化
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .models.chart import Chart, ChartBranch, Song
from .models.enums import BranchType, TargetDifficulty
from .models.result import (
    BranchResult, ChartResult, SongResult,
    DimensionScore, WindowMetrics, CALC_VERSION,
)
from .parsers.tja_parser import TJAParser
from .features.note_features import extract_note_features, NoteFeature
from .analysis.window_analysis import sliding_window_analysis
from .dimensions import get_all_dimensions, BaseDimension
from .aggregation.target_difficulty import aggregate_target_difficulty
from .explanation.explainer import generate_hotspots, generate_summary


class RatingEngine:
    """谱面难度评定引擎。"""

    def __init__(
        self,
        dimensions: list[BaseDimension] | None = None,
        hotspot_count: int = 5,
    ):
        self.dimensions = dimensions or get_all_dimensions()
        self.hotspot_count = hotspot_count
        self._parser = TJAParser()

    # ---- 高层 API ----

    def rate_file(self, path: str | Path) -> SongResult:
        """从文件路径读入并评定整首歌。"""
        song = self._parser.parse_file(path)
        return self.rate_song(song)

    def rate_song(self, song: Song) -> SongResult:
        """评定一首歌曲下所有谱面。"""
        chart_results: list[ChartResult] = []
        for chart in song.charts:
            cr = self.rate_chart(chart)
            chart_results.append(cr)

        overview_parts: list[str] = []
        for cr in chart_results:
            for br in cr.branch_results:
                td = br.target_difficulties
                overview_parts.append(
                    f"{cr.course.label}/{br.branch_type.value}: "
                    f"过关={td.get(TargetDifficulty.PASS, 0):.2f} "
                    f"全连={td.get(TargetDifficulty.FULL_COMBO, 0):.2f} "
                    f"精度={td.get(TargetDifficulty.HIGH_ACCURACY, 0):.2f}"
                )

        return SongResult(
            title=song.title,
            chart_results=chart_results,
            overview="\n".join(overview_parts),
        )

    def rate_chart(self, chart: Chart) -> ChartResult:
        """评定一张谱面（含所有分支）。"""
        branch_results: list[BranchResult] = []
        for bt, branch in chart.branches.items():
            br = self.rate_branch(branch, chart)
            branch_results.append(br)

        return ChartResult(
            song_title=chart.info.title,
            course=chart.info.course,
            branch_results=branch_results,
        )

    def rate_branch(self, branch: ChartBranch, chart: Chart) -> BranchResult:
        """评定单个分支 — 核心流程。"""
        info = chart.info

        # 第1层：音符级特征提取
        features = extract_note_features(branch)

        if not features:
            return BranchResult(
                song_title=info.title,
                course=info.course,
                branch_type=branch.branch_type,
                summary="谱面无有效击打音符",
                missing_fields=chart.missing_fields,
            )

        # 第2层：段落级滑窗分析
        window_metrics = sliding_window_analysis(features)

        # 第3层（维度计算 + 聚合）
        dim_scores: list[DimensionScore] = []
        for dim in self.dimensions:
            score = dim.compute(features, window_metrics)
            dim_scores.append(score)

        # 聚合为三类目标难度
        target_diffs = aggregate_target_difficulty(dim_scores)

        # 难点窗口
        hotspots = generate_hotspots(window_metrics, dim_scores, self.hotspot_count)

        # 统计信息
        stats = self._compute_stats(features, branch)

        result = BranchResult(
            song_title=info.title,
            course=info.course,
            branch_type=branch.branch_type,
            target_difficulties=target_diffs,
            dimensions=dim_scores,
            hotspots=hotspots,
            window_metrics=window_metrics,
            stats=stats,
            missing_fields=chart.missing_fields,
        )

        result.summary = generate_summary(result)
        return result

    def _compute_stats(
        self, features: list[NoteFeature], branch: ChartBranch,
    ) -> dict[str, Any]:
        """计算基础统计信息。"""
        if not features:
            return {}

        import numpy as np
        rates = [f.instant_rate for f in features]
        intervals = [f.interval for f in features if f.interval < 100]

        return {
            "total_notes": len(branch.notes),
            "hit_notes": len(features),
            "duration_sec": round(branch.duration, 2),
            "mean_rate": round(float(np.mean(rates)), 3) if rates else 0,
            "max_rate": round(float(np.max(rates)), 3) if rates else 0,
            "median_interval_ms": round(float(np.median(intervals)) * 1000, 1) if intervals else 0,
            "bpm_range": [
                round(min(f.bpm for f in features), 1),
                round(max(f.bpm for f in features), 1),
            ],
            "color_switches": sum(1 for f in features if f.color_switch),
        }
