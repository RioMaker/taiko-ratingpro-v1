"""特征提取测试。"""

import pytest
from taiko_rating.features.note_features import extract_note_features, features_to_arrays
from taiko_rating.models.chart import ChartBranch
from taiko_rating.models.enums import BranchType


class TestNoteFeatureExtraction:
    def test_basic_extraction(self, simple_branch):
        features = extract_note_features(simple_branch)
        assert len(features) == 8

    def test_feature_times(self, simple_branch):
        features = extract_note_features(simple_branch)
        for i in range(1, len(features)):
            assert features[i].time > features[i - 1].time

    def test_intervals(self, simple_branch):
        features = extract_note_features(simple_branch)
        # 第一个音符间隔为 inf
        assert features[0].interval == float("inf")
        # 后续音符间隔为正数
        for f in features[1:]:
            assert f.interval > 0

    def test_color_switches(self, simple_branch):
        features = extract_note_features(simple_branch)
        # simple_branch 交替 don/ka，所以第二个起都是切换
        for f in features[1:]:
            assert f.color_switch is True

    def test_instant_rate(self, simple_branch):
        features = extract_note_features(simple_branch)
        # 第一个音符速率为 0
        assert features[0].instant_rate == 0.0
        # 后续音符速率 > 0
        for f in features[1:]:
            assert f.instant_rate > 0

    def test_dense_branch_rates(self, dense_branch):
        features = extract_note_features(dense_branch)
        assert len(features) == 32
        # 高密度分支速率应高于简单分支
        rates = [f.instant_rate for f in features[1:]]
        assert max(rates) > 10.0

    def test_window_rates(self, simple_branch):
        features = extract_note_features(simple_branch)
        # 前几个音符的窗口速率可能为 0（不够窗口大小）
        assert features[0].window4_rate == 0.0
        # 后面的应有值
        assert features[-1].window4_rate > 0.0

    def test_empty_branch(self):
        branch = ChartBranch(branch_type=BranchType.NONE)
        features = extract_note_features(branch)
        assert features == []

    def test_features_to_arrays(self, simple_branch):
        features = extract_note_features(simple_branch)
        arrays = features_to_arrays(features)
        assert "time" in arrays
        assert "interval" in arrays
        assert len(arrays["time"]) == 8

    def test_features_to_arrays_empty(self):
        arrays = features_to_arrays([])
        assert arrays == {}
