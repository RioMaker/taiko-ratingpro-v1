"""CLI 入口 — 太鼓达人谱面难度评定工具。

用法:
  taiko-rating <tja_file> [--json] [--pretty]
  taiko-rating batch <directory> [--json] [--output <file>]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .engine import RatingEngine


def main(argv: list[str] | None = None) -> None:
    args_list = argv if argv is not None else sys.argv[1:]

    # 检测是否使用子命令
    if args_list and args_list[0] == "batch":
        _main_batch(args_list[1:])
    else:
        _main_rate(args_list)


def _main_rate(args_list: list[str]) -> None:
    parser = argparse.ArgumentParser(
        prog="taiko-rating",
        description="太鼓达人谱面多维难度评定系统",
    )
    parser.add_argument("file", help="TJA 谱面文件路径")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出")
    parser.add_argument("--pretty", action="store_true", help="格式化输出")
    parser.add_argument("--encoding", default="utf-8", help="文件编码 (默认 utf-8)")

    args = parser.parse_args(args_list)
    engine = RatingEngine()
    _run_single(engine, args)


def _main_batch(args_list: list[str]) -> None:
    parser = argparse.ArgumentParser(
        prog="taiko-rating batch",
        description="批量评定目录下所有 TJA 文件",
    )
    parser.add_argument("directory", help="包含 TJA 文件的目录路径")
    parser.add_argument("--json", action="store_true", dest="batch_json",
                        help="以 JSON 输出")
    parser.add_argument("--output", "-o", help="输出文件路径")
    parser.add_argument("--encoding", default="utf-8", help="文件编码")

    args = parser.parse_args(args_list)
    engine = RatingEngine()
    _run_batch(engine, args)


def _run_single(engine: RatingEngine, args: argparse.Namespace) -> None:
    path = Path(args.file)
    if not path.exists():
        print(f"错误: 文件不存在 — {path}", file=sys.stderr)
        sys.exit(1)

    result = engine.rate_file(path)

    if args.json or args.pretty:
        data = result.to_dict()
        indent = 2 if args.pretty else None
        print(json.dumps(data, indent=indent, ensure_ascii=False))
    else:
        _print_result_text(result)


def _run_batch(engine: RatingEngine, args: argparse.Namespace) -> None:
    directory = Path(args.directory)
    if not directory.is_dir():
        print(f"错误: 目录不存在 — {directory}", file=sys.stderr)
        sys.exit(1)

    tja_files = sorted(directory.rglob("*.tja"))
    if not tja_files:
        print(f"未找到 TJA 文件: {directory}", file=sys.stderr)
        sys.exit(1)

    all_results = []
    for tja_path in tja_files:
        try:
            result = engine.rate_file(tja_path)
            all_results.append(result)
            print(f"✓ {tja_path.name}: {len(result.chart_results)} 谱面已评定")
        except Exception as e:
            print(f"✗ {tja_path.name}: {e}", file=sys.stderr)

    if args.batch_json and args.output:
        data = [r.to_dict() for r in all_results]
        output_path = Path(args.output)
        output_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"\n结果已写入: {output_path}")
    elif args.batch_json:
        data = [r.to_dict() for r in all_results]
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        for result in all_results:
            _print_result_text(result)
            print("=" * 60)


def _print_result_text(result) -> None:
    """以人类可读格式输出评定结果。"""
    print(f"\n{'='*60}")
    print(f"歌曲: {result.title}")
    print(f"{'='*60}")

    for cr in result.chart_results:
        for br in cr.branch_results:
            print(f"\n--- {cr.course.label} / {br.branch_type.value} ---")
            print(f"  计算版本: {br.calc_version}")

            if br.stats:
                s = br.stats
                print(f"  击打数: {s.get('hit_notes', 0)}, "
                      f"时长: {s.get('duration_sec', 0)}s, "
                      f"BPM: {s.get('bpm_range', [0,0])}")

            print("\n  [目标难度]")
            for t, v in br.target_difficulties.items():
                label = {"pass": "过关", "fc": "全连", "acc": "高精度"}.get(t.value, t.value)
                bar = "█" * int(v) + "░" * (10 - int(v))
                print(f"    {label:6s}: {v:5.2f}/10  |{bar}|")

            print("\n  [维度评分]")
            for d in br.dimensions:
                bar = "█" * int(d.normalized) + "░" * (10 - int(d.normalized))
                print(f"    {d.name:26s}: {d.normalized:5.2f}/10  |{bar}|")

            if br.hotspots:
                print(f"\n  [难点窗口] (top {len(br.hotspots)})")
                for i, h in enumerate(br.hotspots, 1):
                    print(f"    {i}. {h.start_time:.1f}s ~ {h.end_time:.1f}s  "
                          f"(严重度 {h.severity:.2f})")
                    print(f"       主维度: {', '.join(h.primary_dimensions)}")
                    print(f"       {h.explanation}")

            if br.missing_fields:
                print(f"\n  ⚠ 缺失字段: {', '.join(br.missing_fields)}")

            print(f"\n  {br.summary}")

    if result.overview:
        print(f"\n[概览]\n{result.overview}")


if __name__ == "__main__":
    main()
