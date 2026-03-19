"""枚举定义：音符类型、难度等级、分支类型等。"""

from enum import Enum, IntEnum


class NoteType(IntEnum):
    """TJA 音符类型编码。"""
    REST = 0
    DON = 1          # 咚（小）
    KA = 2           # 咔（小）
    DON_BIG = 3      # 咚（大）
    KA_BIG = 4       # 咔（大）
    DRUMROLL = 5     # 连打开始
    DRUMROLL_BIG = 6 # 连打开始（大）
    BALLOON = 7      # 气球
    END_SPECIAL = 8  # 连打/气球结束
    KUSUDAMA = 9     # 彩球

    @property
    def is_hit(self) -> bool:
        """是否为需要击打判定的音符（咚/咔）。"""
        return self in (NoteType.DON, NoteType.KA, NoteType.DON_BIG, NoteType.KA_BIG)

    @property
    def is_don(self) -> bool:
        return self in (NoteType.DON, NoteType.DON_BIG)

    @property
    def is_ka(self) -> bool:
        return self in (NoteType.KA, NoteType.KA_BIG)

    @property
    def is_big(self) -> bool:
        return self in (NoteType.DON_BIG, NoteType.KA_BIG, NoteType.DRUMROLL_BIG)

    @property
    def is_special(self) -> bool:
        return self in (NoteType.DRUMROLL, NoteType.DRUMROLL_BIG,
                        NoteType.BALLOON, NoteType.KUSUDAMA)

    @property
    def color(self) -> str | None:
        """返回 'don' / 'ka' / None。"""
        if self.is_don:
            return "don"
        if self.is_ka:
            return "ka"
        return None


class Course(IntEnum):
    """课程（难度等级）。"""
    EASY = 0
    NORMAL = 1
    HARD = 2
    ONI = 3
    URA = 4   # 里谱面 / Edit

    @property
    def label(self) -> str:
        return {0: "Easy", 1: "Normal", 2: "Hard", 3: "Oni", 4: "Ura"}[self.value]


class BranchType(str, Enum):
    """分支类型。"""
    NORMAL = "N"
    EXPERT = "E"
    MASTER = "M"
    NONE = "NONE"  # 无分支


class TargetDifficulty(str, Enum):
    """三类目标难度。"""
    PASS = "pass"           # 过关难度
    FULL_COMBO = "fc"       # 全连难度
    HIGH_ACCURACY = "acc"   # 高精度难度
