"""维度计算测试。"""

import pytest
from taiko_rating.dimensions import get_all_dimensions
from taiko_rating.features.note_features import extract_note_features
from taiko_rating.analysis.window_analysis import sliding_window_analysis
from taiko_rating.models.chart import ChartBranch
from taiko_rating.models.enums import BranchType


class TestAllDimensions:
    def test_all_seven_dimensions(self):
        dims = get_all_dimensions()
        assert len(dims) == 7
        names = [d.name for d in dims]
        assert "peak_pressure" in names
        assert "sustained_pressure" in names
        assert "technique_complexity" in names
        assert "rhythm_complexity" in names
        assert "reading_complexity" in names
        assert "accuracy_pressure" in names
        assert "miss_penalty" in names

    def test_compute_on_simple(self, simple_branch):
        features = extract_note_features(simple_branch)
        window_metrics = sliding_window_analysis(features)
        dims = get_all_dimensions()
        for dim in dims:
            score = dim.compute(features, window_metrics)
            assert score.name == dim.name
            assert 0 <= score.normalized <= 10
            assert isinstance(score.raw_value, float)

    def test_compute_on_dense(self, dense_branch):
        features = extract_note_features(dense_branch)
        window_metrics = sliding_window_analysis(features)
        dims = get_all_dimensions()
        for dim in dims:
            score = dim.compute(features, window_metrics)
            assert 0 <= score.normalized <= 10

    def test_dense_harder_than_simple(self, simple_branch, dense_branch):
        simple_feats = extract_note_features(simple_branch)
        dense_feats = extract_note_features(dense_branch)
        simple_wm = sliding_window_analysis(simple_feats)
        dense_wm = sliding_window_analysis(dense_feats)

        dims = get_all_dimensions()
        # 至少峰值输出压力应该高密 > 简单
        peak = dims[0]  # peak_pressure
        s_score = peak.compute(simple_feats, simple_wm)
        d_score = peak.compute(dense_feats, dense_wm)
        assert d_score.normalized >= s_score.normalized

    def test_empty_features(self):
        dims = get_all_dimensions()
        for dim in dims:
            score = dim.compute([], [])
            assert score.normalized == 0.0

    def test_dimension_details(self, dense_branch):
        features = extract_note_features(dense_branch)
        window_metrics = sliding_window_analysis(features)
        dims = get_all_dimensions()
        for dim in dims:
            score = dim.compute(features, window_metrics)
            assert isinstance(score.details, dict)


class TestPeakPressure:
    def test_high_rate_gives_high_score(self, dense_branch):
        from taiko_rating.dimensions.peak_pressure import PeakPressure
        features = extract_note_features(dense_branch)
        wm = sliding_window_analysis(features)
        dim = PeakPressure()
        score = dim.compute(features, wm)
        # 高密度 BPM=200 十六分音符应有较高峰值压力
        assert score.normalized > 2.0


class TestSustainedPressure:
    def test_sustained_high_density(self, dense_branch):
        from taiko_rating.dimensions.sustained_pressure import SustainedPressure
        features = extract_note_features(dense_branch)
        wm = sliding_window_analysis(features)
        dim = SustainedPressure()
        score = dim.compute(features, wm)
        assert score.normalized >= 0.0


class TestRhythmComplexity:
    def test_uniform_rhythm_low_complexity(self, simple_branch):
        from taiko_rating.dimensions.rhythm_complexity import RhythmComplexity
        features = extract_note_features(simple_branch)
        wm = sliding_window_analysis(features)
        dim = RhythmComplexity()
        score = dim.compute(features, wm)
        # 等间隔节奏应该复杂度较低
        assert score.normalized < 5.0
