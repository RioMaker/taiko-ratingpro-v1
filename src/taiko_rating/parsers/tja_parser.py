"""TJA 谱面格式解析器。

支持标准 TJA 格式的核心命令：
  TITLE, SUBTITLE, BPM, OFFSET, COURSE, LEVEL, BALLOON,
  GENRE, MAKER, SIDE, DEMOSTART, SCOREINIT, SCOREDIFF,
  #START, #END, #MEASURE, #BPMCHANGE, #SCROLL, #GOGOSTART,
  #GOGOEND, #BRANCHSTART, #BRANCHEND, #N, #E, #M, #DELAY,
  #BARLINEOFF, #BARLINEON
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TextIO

from ..models.chart import Note, ChartBranch, ChartInfo, Chart, Song
from ..models.enums import NoteType, Course, BranchType


_COURSE_MAP = {
    "easy": Course.EASY, "0": Course.EASY,
    "normal": Course.NORMAL, "1": Course.NORMAL,
    "hard": Course.HARD, "2": Course.HARD,
    "oni": Course.ONI, "3": Course.ONI,
    "edit": Course.URA, "ura": Course.URA, "4": Course.URA,
}


class TJAParser:
    """将 TJA 文件解析为内部标准 Chart / Song 结构。"""

    def parse_file(self, path: str | Path, encoding: str = "utf-8") -> Song:
        path = Path(path)
        for enc in (encoding, "shift_jis", "utf-8-sig"):
            try:
                text = path.read_text(encoding=enc)
                break
            except (UnicodeDecodeError, LookupError):
                continue
        else:
            raise ValueError(f"无法以任何支持的编码读取文件: {path}")
        return self.parse_text(text, source=str(path))

    def parse_text(self, text: str, source: str = "<string>") -> Song:
        lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        song = Song()
        global_meta: dict[str, str] = {}
        charts: list[Chart] = []
        current_chart_lines: list[str] | None = None
        chart_meta: dict[str, str] = {}
        in_chart = False

        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("//"):
                continue

            # 头部元数据
            if not in_chart and ":" in stripped and not stripped.startswith("#"):
                key, _, val = stripped.partition(":")
                key = key.strip().upper()
                val = val.strip()
                if key == "TITLE":
                    song.title = val
                    global_meta[key] = val
                else:
                    global_meta[key] = val
                    chart_meta[key] = val
                continue

            # 科目内元数据（COURSE, LEVEL 等可出现在 #START 之前）
            if not in_chart and ":" in stripped and not stripped.startswith("#"):
                key, _, val = stripped.partition(":")
                chart_meta[key.strip().upper()] = val.strip()
                continue

            if ":" in stripped and not stripped.startswith("#") and not in_chart:
                key, _, val = stripped.partition(":")
                chart_meta[key.strip().upper()] = val.strip()
                continue

            if stripped.upper().startswith("COURSE") and ":" in stripped:
                _, _, val = stripped.partition(":")
                chart_meta["COURSE"] = val.strip()
                continue
            if stripped.upper().startswith("LEVEL") and ":" in stripped:
                _, _, val = stripped.partition(":")
                chart_meta["LEVEL"] = val.strip()
                continue
            if stripped.upper().startswith("BALLOON") and ":" in stripped:
                _, _, val = stripped.partition(":")
                chart_meta["BALLOON"] = val.strip()
                continue
            if stripped.upper().startswith("SCOREINIT") and ":" in stripped:
                _, _, val = stripped.partition(":")
                chart_meta["SCOREINIT"] = val.strip()
                continue
            if stripped.upper().startswith("SCOREDIFF") and ":" in stripped:
                _, _, val = stripped.partition(":")
                chart_meta["SCOREDIFF"] = val.strip()
                continue

            if stripped.upper() == "#START" or stripped.upper().startswith("#START "):
                in_chart = True
                current_chart_lines = []
                continue

            if stripped.upper() == "#END":
                if current_chart_lines is not None:
                    chart = self._build_chart(
                        current_chart_lines,
                        {**global_meta, **chart_meta},
                    )
                    charts.append(chart)
                in_chart = False
                current_chart_lines = None
                # 如果下一个谱面还会出现 COURSE: 等，重置 chart_meta
                chart_meta = {}
                continue

            if in_chart and current_chart_lines is not None:
                current_chart_lines.append(stripped)

        song.charts = charts
        if not song.title:
            song.title = source
        return song

    # ------------------------------------------------------------------
    def _build_chart(self, lines: list[str], meta: dict[str, str]) -> Chart:
        info = ChartInfo()
        info.title = meta.get("TITLE", "")
        info.subtitle = meta.get("SUBTITLE", "")
        info.genre = meta.get("GENRE", "")
        info.maker = meta.get("MAKER", "")
        info.song_file = meta.get("WAVE", "")
        info.side = meta.get("SIDE", "")
        info.offset = _float(meta.get("OFFSET", "0"))
        info.demo_start = _float(meta.get("DEMOSTART", "0"))

        course_str = meta.get("COURSE", "oni").strip().lower()
        info.course = _COURSE_MAP.get(course_str, Course.ONI)
        info.level = int(meta.get("LEVEL", "0") or "0")

        balloon_str = meta.get("BALLOON", "")
        balloon_counts = [int(x) for x in re.findall(r"\d+", balloon_str)]

        missing: list[str] = []
        if "BPM" not in meta:
            missing.append("BPM")
        if "OFFSET" not in meta:
            missing.append("OFFSET")

        bpm = _float(meta.get("BPM", "120"))
        offset = info.offset

        chart = Chart(info=info, missing_fields=missing)

        # 解析音符数据
        branches = self._parse_note_data(lines, bpm, offset, balloon_counts)
        if not branches:
            # 没有分支命令 → 全部视为无分支
            branch = self._parse_branch_notes(lines, bpm, offset, balloon_counts)
            chart.branches[BranchType.NONE] = branch
            chart.has_branches = False
        else:
            chart.branches = branches
            chart.has_branches = len(branches) > 1

        return chart

    def _parse_note_data(
        self, lines: list[str], bpm: float, offset: float,
        balloon_counts: list[int],
    ) -> dict[BranchType, ChartBranch]:
        """检测是否存在分支命令并分别解析。"""
        has_branch = any(
            line.upper().startswith("#BRANCHSTART") for line in lines
        )
        if not has_branch:
            return {}

        branches: dict[BranchType, list[str]] = {
            BranchType.NORMAL: [],
            BranchType.EXPERT: [],
            BranchType.MASTER: [],
        }
        common_lines: list[str] = []
        current_branch: BranchType | None = None
        in_branch = False

        for line in lines:
            upper = line.upper()
            if upper.startswith("#BRANCHSTART"):
                in_branch = True
                current_branch = None
                continue
            if upper == "#BRANCHEND":
                in_branch = False
                current_branch = None
                continue
            if upper == "#N":
                current_branch = BranchType.NORMAL
                continue
            if upper == "#E":
                current_branch = BranchType.EXPERT
                continue
            if upper == "#M":
                current_branch = BranchType.MASTER
                continue

            if in_branch and current_branch is not None:
                branches[current_branch].append(line)
            else:
                common_lines.append(line)

        result: dict[BranchType, ChartBranch] = {}
        for bt, blines in branches.items():
            full_lines = common_lines + blines
            if blines:
                result[bt] = self._parse_branch_notes(
                    full_lines, bpm, offset, list(balloon_counts),
                )
        return result

    def _parse_branch_notes(
        self, lines: list[str], init_bpm: float, offset: float,
        balloon_counts: list[int],
    ) -> ChartBranch:
        notes: list[Note] = []
        bpm = init_bpm
        scroll = 1.0
        measure_num = 0
        time_sig = (4, 4)
        current_time = -offset
        balloon_idx = 0
        delay_acc = 0.0

        # 收集每小节的数据
        measure_buf: list[str] = []

        def flush_measure():
            nonlocal current_time, measure_num, balloon_idx
            note_chars = "".join(measure_buf)
            if not note_chars:
                # 空小节，推进时间
                beats = time_sig[0] * (4 / time_sig[1])
                current_time += beats * 60.0 / bpm
                measure_num += 1
                return

            subdivisions = len(note_chars)
            beats = time_sig[0] * (4 / time_sig[1])
            measure_duration = beats * 60.0 / bpm
            sub_duration = measure_duration / subdivisions if subdivisions > 0 else 0

            for i, ch in enumerate(note_chars):
                nt = int(ch) if ch.isdigit() else 0
                if nt == 0:
                    continue
                note_type = NoteType(nt)
                t = current_time + i * sub_duration + delay_acc

                b_count = 0
                if note_type in (NoteType.BALLOON, NoteType.KUSUDAMA):
                    if balloon_idx < len(balloon_counts):
                        b_count = balloon_counts[balloon_idx]
                        balloon_idx += 1

                beat_pos = (i / subdivisions) if subdivisions > 0 else 0.0

                notes.append(Note(
                    time=t,
                    note_type=note_type,
                    bpm=bpm,
                    scroll=scroll,
                    measure_num=measure_num,
                    beat_pos=beat_pos,
                    time_signature=time_sig,
                    balloon_count=b_count,
                ))

            current_time += measure_duration
            measure_num += 1

        for line in lines:
            upper = line.upper()

            # 命令处理
            if upper.startswith("#BPMCHANGE"):
                val = _extract_value(line)
                if val is not None:
                    bpm = val
                continue
            if upper.startswith("#SCROLL"):
                val = _extract_value(line)
                if val is not None:
                    scroll = val
                continue
            if upper.startswith("#MEASURE"):
                parts = line.split(None, 1)
                if len(parts) > 1:
                    m = re.match(r"(\d+)\s*/\s*(\d+)", parts[1])
                    if m:
                        time_sig = (int(m.group(1)), int(m.group(2)))
                continue
            if upper.startswith("#DELAY"):
                val = _extract_value(line)
                if val is not None:
                    delay_acc += val
                continue
            if upper.startswith("#"):
                # 其他命令忽略
                continue

            # 音符行：以数字组成，以逗号结束表示小节结束
            note_part = line.split("//")[0].strip()
            if "," in note_part:
                parts = note_part.split(",")
                for j, part in enumerate(parts):
                    digits = re.sub(r"[^0-9]", "", part)
                    if digits:
                        measure_buf.append(digits)
                    if j < len(parts) - 1:
                        flush_measure()
                        measure_buf = []
            else:
                digits = re.sub(r"[^0-9]", "", note_part)
                if digits:
                    measure_buf.append(digits)

        # 处理最后一个小节
        if measure_buf:
            flush_measure()

        branch = ChartBranch(branch_type=BranchType.NONE, notes=notes)
        return branch


def _float(s: str) -> float:
    try:
        return float(s)
    except (ValueError, TypeError):
        return 0.0


def _extract_value(line: str) -> float | None:
    parts = line.split(None, 1)
    if len(parts) > 1:
        try:
            return float(parts[1].strip())
        except ValueError:
            return None
    return None
