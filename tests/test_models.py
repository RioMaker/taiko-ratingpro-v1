"""数据模型测试。"""

import pytest
from taiko_rating.models.chart import Note, ChartBranch, ChartInfo, Chart, Song
from taiko_rating.models.enums import NoteType, Course, BranchType, TargetDifficulty
from taiko_rating.models.result import DimensionScore, BranchResult, SongResult, CALC_VERSION


class TestNoteType:
    def test_hit_notes(self):
        assert NoteType.DON.is_hit
        assert NoteType.KA.is_hit
        assert NoteType.DON_BIG.is_hit
        assert NoteType.KA_BIG.is_hit
        assert not NoteType.REST.is_hit
        assert not NoteType.DRUMROLL.is_hit
        assert not NoteType.BALLOON.is_hit

    def test_color(self):
        assert NoteType.DON.color == "don"
        assert NoteType.DON_BIG.color == "don"
        assert NoteType.KA.color == "ka"
        assert NoteType.KA_BIG.color == "ka"
        assert NoteType.REST.color is None

    def test_is_big(self):
        assert NoteType.DON_BIG.is_big
        assert NoteType.KA_BIG.is_big
        assert not NoteType.DON.is_big

    def test_is_special(self):
        assert NoteType.BALLOON.is_special
        assert NoteType.DRUMROLL.is_special
        assert not NoteType.DON.is_special


class TestChartBranch:
    def test_empty_branch(self):
        branch = ChartBranch(branch_type=BranchType.NONE)
        assert branch.hit_notes == []
        assert branch.duration == 0.0
        assert branch.total_hits == 0

    def test_hit_notes_filter(self, simple_branch):
        hits = simple_branch.hit_notes
        assert len(hits) == 8
        for h in hits:
            assert h.note_type.is_hit

    def test_duration(self, simple_branch):
        assert simple_branch.duration > 0


class TestChart:
    def test_default_branch(self, simple_chart):
        assert simple_chart.default_branch is not None
        assert simple_chart.default_branch.branch_type == BranchType.NONE

    def test_no_branches(self):
        chart = Chart()
        assert chart.default_branch is None


class TestCourse:
    def test_labels(self):
        assert Course.EASY.label == "Easy"
        assert Course.ONI.label == "Oni"
        assert Course.URA.label == "Ura"


class TestResult:
    def test_branch_result_to_dict(self):
        br = BranchResult(
            song_title="Test",
            course=Course.ONI,
            branch_type=BranchType.NONE,
            target_difficulties={
                TargetDifficulty.PASS: 5.0,
                TargetDifficulty.FULL_COMBO: 6.0,
                TargetDifficulty.HIGH_ACCURACY: 7.0,
            },
            dimensions=[
                DimensionScore(name="peak_pressure", raw_value=3.0, normalized=5.0),
            ],
        )
        d = br.to_dict()
        assert d["song_title"] == "Test"
        assert d["target_difficulties"]["pass"] == 5.0
        assert d["calc_version"] == CALC_VERSION

    def test_dimension_by_name(self):
        br = BranchResult(
            song_title="T", course=Course.ONI, branch_type=BranchType.NONE,
            dimensions=[
                DimensionScore(name="peak_pressure", raw_value=1.0, normalized=2.0),
                DimensionScore(name="rhythm_complexity", raw_value=3.0, normalized=4.0),
            ],
        )
        assert br.dimension_by_name("peak_pressure").normalized == 2.0
        assert br.dimension_by_name("nonexistent") is None

    def test_song_result_to_dict(self):
        sr = SongResult(title="Song A")
        d = sr.to_dict()
        assert d["title"] == "Song A"
        assert d["charts"] == []
