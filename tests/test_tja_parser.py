"""TJA 解析器测试。"""

import pytest
from taiko_rating.parsers.tja_parser import TJAParser
from taiko_rating.models.enums import NoteType, Course, BranchType


class TestTJAParser:
    def setup_method(self):
        self.parser = TJAParser()

    def test_parse_sample_easy(self, sample_easy_path):
        song = self.parser.parse_file(sample_easy_path)
        assert song.title == "Sample Easy Song"
        assert len(song.charts) >= 1

    def test_parse_easy_course(self, sample_easy_path):
        song = self.parser.parse_file(sample_easy_path)
        courses = [c.info.course for c in song.charts]
        assert Course.EASY in courses

    def test_parse_oni_course(self, sample_easy_path):
        song = self.parser.parse_file(sample_easy_path)
        courses = [c.info.course for c in song.charts]
        assert Course.ONI in courses

    def test_parse_hard(self, sample_hard_path):
        song = self.parser.parse_file(sample_hard_path)
        assert song.title == "Sample Hard Song"
        assert len(song.charts) >= 1

    def test_parse_minimal(self, sample_minimal_path):
        song = self.parser.parse_file(sample_minimal_path)
        assert len(song.charts) == 1
        chart = song.charts[0]
        branch = chart.default_branch
        assert branch is not None
        # 极短谱面应有音符
        assert len(branch.notes) >= 1

    def test_notes_have_times(self, sample_easy_path):
        song = self.parser.parse_file(sample_easy_path)
        for chart in song.charts:
            branch = chart.default_branch
            if branch:
                for note in branch.hit_notes:
                    assert isinstance(note.time, float)
                    assert note.bpm > 0

    def test_parse_text(self):
        tja = """TITLE:Inline Test
BPM:150
OFFSET:0

COURSE:Oni
LEVEL:7

#START
1121,
1211,
#END
"""
        song = self.parser.parse_text(tja)
        assert song.title == "Inline Test"
        assert len(song.charts) == 1
        chart = song.charts[0]
        assert chart.info.course == Course.ONI
        assert chart.info.level == 7
        branch = chart.default_branch
        assert branch is not None
        assert branch.total_hits > 0

    def test_bpm_change(self):
        tja = """TITLE:BPM Test
BPM:120
OFFSET:0

COURSE:Oni
LEVEL:5

#START
1111,
#BPMCHANGE 180
1111,
#END
"""
        song = self.parser.parse_text(tja)
        chart = song.charts[0]
        branch = chart.default_branch
        notes = branch.hit_notes
        bpms = set(n.bpm for n in notes)
        assert 120.0 in bpms
        assert 180.0 in bpms

    def test_scroll_change(self):
        tja = """TITLE:Scroll Test
BPM:120
OFFSET:0

COURSE:Oni
LEVEL:5

#START
1111,
#SCROLL 2.0
1111,
#END
"""
        song = self.parser.parse_text(tja)
        chart = song.charts[0]
        notes = chart.default_branch.hit_notes
        scrolls = set(n.scroll for n in notes)
        assert 1.0 in scrolls
        assert 2.0 in scrolls

    def test_empty_chart(self):
        tja = """TITLE:Empty
BPM:120
OFFSET:0
COURSE:Oni
LEVEL:1
#START
0000,
0000,
#END
"""
        song = self.parser.parse_text(tja)
        chart = song.charts[0]
        assert chart.default_branch.total_hits == 0

    def test_missing_bpm(self):
        tja = """TITLE:NoBPM
OFFSET:0
COURSE:Oni
LEVEL:1
#START
1111,
#END
"""
        song = self.parser.parse_text(tja)
        chart = song.charts[0]
        assert "BPM" in chart.missing_fields
