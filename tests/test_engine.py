"""引擎集成测试。"""

import pytest
from taiko_rating.engine import RatingEngine
from taiko_rating.models.enums import TargetDifficulty, BranchType


class TestEngineWithFixtures:
    def setup_method(self):
        self.engine = RatingEngine()

    def test_rate_branch(self, simple_branch, simple_chart):
        result = self.engine.rate_branch(simple_branch, simple_chart)
        assert result.song_title == "Test Song"
        assert len(result.dimensions) == 7
        assert TargetDifficulty.PASS in result.target_difficulties
        assert TargetDifficulty.FULL_COMBO in result.target_difficulties
        assert TargetDifficulty.HIGH_ACCURACY in result.target_difficulties

    def test_rate_chart(self, simple_chart):
        result = self.engine.rate_chart(simple_chart)
        assert len(result.branch_results) == 1

    def test_rate_dense(self, dense_branch, dense_chart):
        result = self.engine.rate_branch(dense_branch, dense_chart)
        assert len(result.dimensions) == 7
        # 高密度谱面应有较高的过关难度
        pass_diff = result.target_difficulties[TargetDifficulty.PASS]
        assert pass_diff > 0

    def test_result_has_summary(self, simple_branch, simple_chart):
        result = self.engine.rate_branch(simple_branch, simple_chart)
        assert len(result.summary) > 0

    def test_result_has_stats(self, simple_branch, simple_chart):
        result = self.engine.rate_branch(simple_branch, simple_chart)
        assert "hit_notes" in result.stats
        assert result.stats["hit_notes"] == 8

    def test_result_serializable(self, simple_branch, simple_chart):
        result = self.engine.rate_branch(simple_branch, simple_chart)
        d = result.to_dict()
        assert isinstance(d, dict)
        assert "target_difficulties" in d
        assert "dimensions" in d
        assert "calc_version" in d


class TestEngineWithFiles:
    def setup_method(self):
        self.engine = RatingEngine()

    def test_rate_easy_file(self, sample_easy_path):
        result = self.engine.rate_file(sample_easy_path)
        assert result.title == "Sample Easy Song"
        assert len(result.chart_results) >= 1

    def test_rate_hard_file(self, sample_hard_path):
        result = self.engine.rate_file(sample_hard_path)
        assert result.title == "Sample Hard Song"
        assert len(result.chart_results) >= 1
        # 应有难点窗口
        for cr in result.chart_results:
            for br in cr.branch_results:
                if br.hotspots:
                    assert len(br.hotspots) >= 1
                    h = br.hotspots[0]
                    assert h.end_time > h.start_time
                    assert len(h.primary_dimensions) > 0

    def test_rate_minimal_file(self, sample_minimal_path):
        result = self.engine.rate_file(sample_minimal_path)
        assert len(result.chart_results) == 1

    def test_hard_harder_than_easy(self, sample_easy_path, sample_hard_path):
        easy = self.engine.rate_file(sample_easy_path)
        hard = self.engine.rate_file(sample_hard_path)

        # 找到 Oni 难度
        easy_oni = None
        for cr in easy.chart_results:
            if cr.course.value == 3:  # Oni
                easy_oni = cr.branch_results[0] if cr.branch_results else None

        hard_oni = None
        for cr in hard.chart_results:
            if cr.course.value == 3:
                hard_oni = cr.branch_results[0] if cr.branch_results else None

        if easy_oni and hard_oni:
            # hard 的过关难度应 >= easy
            assert (hard_oni.target_difficulties[TargetDifficulty.PASS]
                    >= easy_oni.target_difficulties[TargetDifficulty.PASS])

    def test_batch_process(self, sample_easy_path, sample_hard_path):
        """测试批量处理多个文件。"""
        results = []
        for path in [sample_easy_path, sample_hard_path]:
            r = self.engine.rate_file(path)
            results.append(r)
        assert len(results) == 2
        assert results[0].title != results[1].title


class TestEdgeCases:
    def setup_method(self):
        self.engine = RatingEngine()

    def test_empty_notes_branch(self):
        from taiko_rating.models.chart import ChartBranch, Chart, ChartInfo
        from taiko_rating.models.enums import Course
        branch = ChartBranch(branch_type=BranchType.NONE, notes=[])
        chart = Chart(info=ChartInfo(title="Empty", course=Course.ONI))
        chart.branches[BranchType.NONE] = branch
        result = self.engine.rate_branch(branch, chart)
        assert result.summary == "谱面无有效击打音符"

    def test_single_note(self):
        from taiko_rating.models.chart import Note, ChartBranch, Chart, ChartInfo
        from taiko_rating.models.enums import NoteType, Course
        note = Note(time=0.0, note_type=NoteType.DON, bpm=120.0)
        branch = ChartBranch(branch_type=BranchType.NONE, notes=[note])
        chart = Chart(info=ChartInfo(title="Single", course=Course.ONI))
        chart.branches[BranchType.NONE] = branch
        result = self.engine.rate_branch(branch, chart)
        # 单音符应该所有维度为 0 或极低
        for dim in result.dimensions:
            assert dim.normalized <= 1.0
