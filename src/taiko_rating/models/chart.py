"""标准化谱面数据结构。

无论输入来源（TJA / JSON / 其他），内部一律使用此数据结构。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .enums import NoteType, Course, BranchType


@dataclass
class Note:
    """单个音符。"""
    time: float                     # 绝对时间（秒）
    note_type: NoteType
    bpm: float                      # 当前 BPM
    scroll: float = 1.0             # HS / 滚动速度
    measure_num: int = 0            # 所在小节号
    beat_pos: float = 0.0           # 小节内拍位（0 ~ 1）
    time_signature: tuple[int, int] = (4, 4)  # 拍号
    is_branch_start: bool = False   # 是否为分支切换点
    balloon_count: int = 0          # 气球连打次数（仅气球音符）
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class ChartBranch:
    """单个谱面分支。"""
    branch_type: BranchType
    notes: list[Note] = field(default_factory=list)

    @property
    def hit_notes(self) -> list[Note]:
        """仅返回需要判定的击打音符。"""
        return [n for n in self.notes if n.note_type.is_hit]

    @property
    def duration(self) -> float:
        """谱面时长（秒）。"""
        if not self.notes:
            return 0.0
        return self.notes[-1].time - self.notes[0].time

    @property
    def total_hits(self) -> int:
        return len(self.hit_notes)


@dataclass
class ChartInfo:
    """谱面元信息。"""
    title: str = ""
    subtitle: str = ""
    course: Course = Course.ONI
    level: int = 0                  # 星级
    genre: str = ""
    maker: str = ""
    song_file: str = ""
    offset: float = 0.0
    demo_start: float = 0.0
    side: str = ""                  # 表/里
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class Chart:
    """一张完整谱面（可含多分支）。"""
    info: ChartInfo = field(default_factory=ChartInfo)
    branches: dict[BranchType, ChartBranch] = field(default_factory=dict)
    has_branches: bool = False
    missing_fields: list[str] = field(default_factory=list)

    @property
    def default_branch(self) -> ChartBranch | None:
        """返回默认分支（无分支谱面返回 NONE，有分支返回 NORMAL）。"""
        if BranchType.NONE in self.branches:
            return self.branches[BranchType.NONE]
        return self.branches.get(BranchType.NORMAL)

    @property
    def all_branches(self) -> list[ChartBranch]:
        return list(self.branches.values())

    def get_branch(self, branch_type: BranchType) -> ChartBranch | None:
        return self.branches.get(branch_type)


@dataclass
class Song:
    """一首歌曲包含的所有谱面。"""
    title: str = ""
    charts: list[Chart] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)
