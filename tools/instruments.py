#!/usr/bin/env python3
"""列出 8 个功能槽可选的乐器，以及各编制预设。

用法:
    python tools/instruments.py                 # 看全部可选
    python tools/instruments.py --preset lofi   # 只看某个预设
    python tools/instruments.py --project projects/demo   # 看某首歌当前实际用什么
"""

import argparse
import os
import sys

_MUSIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "music")
if _MUSIC_DIR not in sys.path:
    sys.path.insert(0, _MUSIC_DIR)

from core.instruments import DEFAULT, INSTRUMENTS, PRESETS, SLOTS, plan  # noqa: E402


def _program_text(slot, entry):
    """perc 这类共用鼓组的槽没有自己的 program，显示"随 drums"而不是瞎编一个号。"""
    if "program" in entry:
        return f"program {entry['program']:>3d}"
    return "鼓组随 drums"


def show_all():
    print("\n每个功能槽可选的乐器（* = 出厂默认）\n")
    for slot in SLOTS:
        print(f"  [{slot}]")
        for key, entry in INSTRUMENTS[slot].items():
            mark = "*" if DEFAULT[slot] == key else " "
            extra = ""
            if entry.get("tweaks"):
                pairs = "、".join(
                    f"{g}.{k}={v}" for g, patch in entry["tweaks"].items() for k, v in patch.items()
                )
                extra = f"  （自带微调: {pairs}）"
            print(f"   {mark} {key:12s} {_program_text(slot, entry):12s}  {entry['name']:10s} {entry['why']}{extra}")
        print()


def show_preset(name):
    if name not in PRESETS:
        print(f"未知预设 {name!r}：可用 {', '.join(PRESETS)}", file=sys.stderr)
        return 1
    print(f"\n预设 [{name}]")
    # 走 plan()，这样 perc 的鼓组号也已经是解析后的真实值
    for slot, entry in plan({"preset": name}).items():
        print(f"  {slot:8s} {entry['key']:14s} {entry['name']:10s} program {entry['program']}")
    print()
    return 0


def show_project(path):
    from core.config import load_config

    cfg = load_config(path)
    print(f"\n{path} 的编制（preset={cfg.get('preset') or '未指定 → 用出厂默认'}）")
    for slot, entry in plan(cfg).items():
        print(f"  {slot:8s} {entry['key']:14s} {entry['name']:10s} program {entry['program']}")
    print()
    return 0


def main():
    parser = argparse.ArgumentParser(description="查看可选的乐器与编制预设")
    parser.add_argument("--preset", default=None, help=f"只看某个预设：{', '.join(PRESETS)}")
    parser.add_argument("--project", default=None, help="看某个项目当前实际使用的编制")
    args = parser.parse_args()

    if args.project:
        return show_project(args.project)
    if args.preset:
        return show_preset(args.preset)

    show_all()
    print("编制预设（可用 config.json 的 preset 字段一次配好）\n")
    for name, mapping in PRESETS.items():
        names = " / ".join(INSTRUMENTS[s][k]["name"] for s, k in mapping.items())
        print(f"  {name:12s} {names}")
    print("\n换某个槽：在 config.json 里写 \"instruments\": {\"chords\": \"nylon\"}")
    print("换整套：写 \"preset\": \"cinematic\"\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
