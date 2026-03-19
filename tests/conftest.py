"""测试共用 fixtures。"""

import pytest
from pathlib import Path

from taiko_rating.models.chart import Note, ChartBranch, ChartInfo, Chart, Song
from taiko_rating.models.enums import NoteType, Course, BranchType


EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"


@pytest.fixture
def sample_easy_path():
    return EXAMPLES_DIR / "sample_easy.tja"


@pytest.fixture
def sample_hard_path():
    return EXAMPLES_DIR / "sample_hard.tja"


@pytest.fixture
def sample_minimal_path():
    return EXAMPLES_DIR / "sample_minimal.tja"


@pytest.fixture
def simple_branch() -> ChartBranch:
    """手工构建一个简单分支：8 个等间隔音符。"""
    notes = []
    bpm = 120.0
    interval = 60.0 / bpm / 2  # 八分音符间隔
    for i in range(8):
        nt = NoteType.DON if i % 2 == 0 else NoteType.KA
        notes.append(Note(
            time=i * interval,
            note_type=nt,
            bpm=bpm,
            scroll=1.0,
            measure_num=i // 4,
            beat_pos=(i % 4) / 4.0,
        ))
    return ChartBranch(branch_type=BranchType.NONE, notes=notes)


@pytest.fixture
def dense_branch() -> ChartBranch:
    """手工构建一个高密度分支：32 个音符，BPM=200。"""
    notes = []
    bpm = 200.0
    interval = 60.0 / bpm / 4  # 十六分音符间隔
    pattern = [NoteType.DON, NoteType.DON, NoteType.KA, NoteType.DON]
    for i in range(32):
        nt = pattern[i % len(pattern)]
        notes.append(Note(
            time=i * interval,
            note_type=nt,
            bpm=bpm,
            scroll=1.0,
            measure_num=i // 16,
            beat_pos=(i % 16) / 16.0,
        ))
    return ChartBranch(branch_type=BranchType.NONE, notes=notes)


@pytest.fixture
def simple_chart(simple_branch) -> Chart:
    info = ChartInfo(title="Test Song", course=Course.ONI, level=5)
    chart = Chart(info=info)
    chart.branches[BranchType.NONE] = simple_branch
    return chart


@pytest.fixture
def dense_chart(dense_branch) -> Chart:
    info = ChartInfo(title="Dense Song", course=Course.ONI, level=10)
    chart = Chart(info=info)
    chart.branches[BranchType.NONE] = dense_branch
    return chart
