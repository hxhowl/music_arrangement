"""作品索引：把 `projects/` 下的每首歌汇总成一张表。

为什么需要：`projects/` 除 demo 外都被 gitignore，换一个窗口、换一个 AI 工具、
或者隔两周回来看，都不知道"我做过哪些歌、各自什么调、最新到第几版"。
索引不解决创作问题，但它让工作区重新可读。

索引是**产物**，每次生成都会重写，不要手改。
"""

import json
import os
import re

INDEX_NAME = "INDEX.md"
_HEADER = (
    "# 作品索引\n\n"
    "> 自动生成，每次生成 MIDI 时重写 —— 不要手改。\n\n"
    "| 目录 | 风格 | 调性 | BPM | 小节 | 最新版本 | 音轨 |\n"
    "|---|---|---|---:|---:|---|---|\n"
)


def _version_number(version: str):
    matched = re.fullmatch(r"v(\d+)", version or "")
    return int(matched.group(1)) if matched else -1


def latest_version(project_dir: str, name: str):
    """扫 output 目录，返回最新版本号（如 "v9"）与它的轨数。没产物就返回 (None, 0)。"""
    out_dir = os.path.join(project_dir, "music", "output")
    if not os.path.isdir(out_dir):
        return None, 0

    best, best_num = None, -1
    for filename in os.listdir(out_dir):
        matched = re.fullmatch(re.escape(name) + r"-(v\d+)\.mid", filename)
        if matched:
            number = _version_number(matched.group(1))
            if number > best_num:
                best, best_num = matched.group(1), number

    tracks = 0
    if best:
        tracks = _count_tracks(os.path.join(out_dir, f"{name}-{best}.mid"))
    return best, tracks


def _count_tracks(mid_path: str) -> int:
    try:
        import pretty_midi

        return len(pretty_midi.PrettyMIDI(mid_path).instruments)
    except Exception:
        return 0


def collect(projects_root: str):
    """扫一层子目录找项目（有 config.json 的才算），返回若干行。"""
    rows = []
    if not os.path.isdir(projects_root):
        return rows

    for entry in sorted(os.listdir(projects_root)):
        project_dir = os.path.join(projects_root, entry)
        config_path = os.path.join(project_dir, "config.json")
        if not os.path.isfile(config_path):
            continue
        try:
            with open(config_path, encoding="utf-8") as f:
                cfg = json.load(f)
        except (OSError, ValueError):
            rows.append(dict(name=entry, broken=True))
            continue

        version, tracks = latest_version(project_dir, entry)
        sections = cfg.get("sections") or {}
        rows.append(dict(
            name=entry,
            style=cfg.get("style", "-"),
            key=cfg.get("key", "-"),
            bpm=cfg.get("bpm", "-"),
            bars=sum(int(v) for v in sections.values()) if sections else "-",
            version=version or "（还没生成）",
            tracks=tracks or "-",
            broken=False,
        ))
    return rows


def render(rows) -> str:
    lines = [_HEADER]
    for row in rows:
        if row["broken"]:
            lines.append(f"| {row['name']} | （config 读取失败） | | | | | |\n")
            continue
        lines.append(
            f"| {row['name']} | {row['style']} | {row['key']} | {row['bpm']} | "
            f"{row['bars']} | {row['version']} | {row['tracks']} |\n"
        )
    if len(rows) == 0:
        lines.append("| （还没有项目） | | | | | | |\n")
    return "".join(lines)


def write(projects_root: str):
    """重写索引，返回路径。任何异常都不该让"生成 MIDI"这件事失败。"""
    path = os.path.join(projects_root, INDEX_NAME)
    try:
        rows = collect(projects_root)
        with open(path, "w", encoding="utf-8") as f:
            f.write(render(rows))
        return path
    except OSError:
        return None
