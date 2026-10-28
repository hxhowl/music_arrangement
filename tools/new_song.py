#!/usr/bin/env python3
"""从一个描述建新项目：目录 + brief.md + config.json + decisions.md。

用法:
    python tools/new_song.py "90秒 亲子短视频 电影感 结尾来点反差" --duration 90
    python tools/new_song.py "慵懒的周末早晨" --style lofi --bpm 76 --key Dm
    python tools/new_song.py --style pop --key C --sections "intro:4,verse:8,chorus:8,outro:4"

没写的参数会按描述里的关键词推断，推断结果会打印出来，可以随时用参数覆盖。
"""

import argparse
import datetime
import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_MUSIC_DIR = os.path.join(_ROOT, "music")
if _MUSIC_DIR not in sys.path:
    sys.path.insert(0, _MUSIC_DIR)

from core.arrange import ARRANGE, TRACK_KEYS  # noqa: E402
from core.styles import STYLES  # noqa: E402
from core.theory import build_progression, default_progression, parse_key  # noqa: E402

# 描述关键词 -> (bpm, style)。顺序即优先级，先命中先用。
RULES = (
    (("无厘头", "反差", "搞笑", "俏皮", "怪", "调皮"), 128, "playful"),
    (("慵懒", "放松", "日常", "生活", "lofi", "lo-fi", "午后"), 76, "lofi"),
    (("电影", "史诗", "悬疑", "悲伤", "离别", "安静", "温柔", "抒情", "慢"), 72, "cinematic"),
    (("欢快", "活泼", "热闹", "快", "节奏", "亲子", "短视频", "轻快"), 120, "pop"),
)

# 没给 --key 时的默认调：小调风格给小调，大调风格给大调
STYLE_DEFAULT_KEY = {
    "cinematic": "Dm",
    "lofi": "Dm",
    "pop": "C",
    "playful": "G",
}


def infer(desc: str):
    """从描述里收集所有命中的 (bpm, style, 关键词)，按 RULES 优先级排序。"""
    text = (desc or "").lower()
    hits = []
    for keywords, bpm, style in RULES:
        for word in keywords:
            if word in text:
                hits.append((bpm, style, word))
                break
    return hits


def parse_sections(text: str):
    """'intro:4,verse:8' -> [(name, bars), ...]，校验段落名与 ARRANGE 对齐。"""
    if not text:
        return [("intro", 4), ("verse", 8), ("chorus", 8), ("outro", 4)]

    result = []
    for chunk in text.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if ":" not in chunk:
            raise ValueError(f"段落写法应为 '名字:小节数'，收到 {chunk!r}")
        name, _, bars = chunk.partition(":")
        name = name.strip()
        if name not in ARRANGE:
            raise ValueError(
                f"未知段落 {name!r}：可选 {', '.join(ARRANGE)}"
                f"（要加新段落请先改 music/core/arrange.py）"
            )
        try:
            count = int(bars)
        except ValueError:
            raise ValueError(f"段落 {name!r} 的小节数必须是整数，收到 {bars!r}")
        if count <= 0:
            raise ValueError(f"段落 {name!r} 的小节数必须为正，收到 {count}")
        result.append((name, count))

    if not result:
        raise ValueError("sections 解析结果为空")
    return result


def fit_sections(bpm: float, seconds: float):
    """按时长反推段落，比例：前奏 15% / 主歌 38% / 副歌 35% / 尾奏 12%。"""
    bar_seconds = 4 * 60.0 / bpm
    total = max(12, int(round(seconds / bar_seconds)))
    intro = max(2, int(round(total * 0.15)))
    outro = max(2, int(round(total * 0.12)))
    rest = max(8, total - intro - outro)
    verse = max(4, int(round(rest * 0.52)))
    chorus = max(4, rest - verse)
    return [("intro", intro), ("verse", verse), ("chorus", chorus), ("outro", outro)]


def unique_project_dir(root: str, slug: str) -> str:
    today = datetime.date.today().strftime("%Y%m%d")
    seq = 1
    while True:
        path = os.path.join(root, f"{today}-{slug}-{seq:03d}")
        if not os.path.exists(path):
            return path
        seq += 1


def build_brief(title, desc, cfg, sections, resolved, project_name):
    bar_seconds = 4 * 60.0 / cfg["bpm"]
    total_bars = sum(bars for _, bars in sections)
    total_seconds = total_bars * bar_seconds

    lines = [
        f"# {title}",
        "",
        f"> {desc}" if desc else "> （待补充一句话创作意图）",
        "",
        "## 参数",
        "",
        "| 项 | 值 |",
        "|---|---|",
        f"| 风格 | `{cfg['style']}` |",
        f"| 调性 | `{cfg['key']}` |",
        f"| 和弦进行 | {' - '.join(resolved)} |",
        f"| BPM | {cfg['bpm']} |",
        f"| 时长 | 约 {total_seconds:.0f} 秒（{total_bars} 小节，{bar_seconds:.2f} 秒/小节） |",
        "",
        "## 段落",
        "",
        "| 段落 | 小节 | 起始小节 |",
        "|---|---|---|",
    ]

    offset = 1
    for name, bars in sections:
        lines.append(f"| {name} | {bars} | 第 {offset} 小节 |")
        offset += bars

    lines += [
        "",
        "## 音轨规划",
        "",
        "由 `music/core/arrange.py` 的 `ARRANGE` 决定，风格决定每档具体怎么打。",
        "",
        "| 段落 | " + " | ".join(TRACK_KEYS) + " | 力度 |",
        "|---|" + "---|" * len(TRACK_KEYS) + "---|",
    ]
    for name, _ in sections:
        arr = ARRANGE[name]
        cells = []
        for key in TRACK_KEYS:
            value = arr.get(key)
            cells.append("—" if not value else (value if isinstance(value, str) else "✓"))
        lines.append(f"| {name} | " + " | ".join(cells) + f" | {arr['vel']:.2f} |")

    lines += [
        "",
        "## 下一步",
        "",
        "```bash",
        f"bash tools/compose.sh projects/{project_name}",
        "```",
        "",
        "然后把 `music/output/<name>-v1.mid` 拖进 Logic Pro，换音色、调力度、加自动化。",
        "改动理由写进同目录的 `decisions.md`。",
        "",
        "## 必须真人完成的部分",
        "",
        "- 人声（本链路不生成人声）",
        "- 音色与混音决策",
        "- 最终成品是否可用",
        "",
    ]
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="从一句话建一个新的编曲项目")
    parser.add_argument("desc", nargs="?", default="", help="一句话描述，如 \"90秒 亲子 电影感\"")
    parser.add_argument("--title", default=None, help="曲名，默认用描述前 20 字")
    parser.add_argument("--slug", default=None, help="目录名后缀，默认用风格名")
    parser.add_argument("--bpm", type=int, default=None)
    parser.add_argument("--key", default=None, help="调性，如 Am / C / F#m")
    parser.add_argument("--style", default=None, help=f"风格：{', '.join(STYLES)}")
    parser.add_argument("--progression", default=None,
                        help="级数进行，逗号分隔，如 i,VI,III,VII")
    parser.add_argument("--sections", default=None, help="段落，如 intro:4,verse:8,chorus:8,outro:4")
    parser.add_argument("--duration", type=float, default=None, help="目标时长（秒），自动反推段落")
    parser.add_argument("--root", default=os.path.join(_ROOT, "projects"), help="项目根目录")
    args = parser.parse_args(argv)

    try:
        hits = infer(args.desc)
        style = args.style or (hits[0][1] if hits else "cinematic")
        bpm = args.bpm or (hits[0][0] if hits else 84)
        # 调性不猜情绪，只跟风格走：小调风格给小调，大调风格给大调
        key = args.key or STYLE_DEFAULT_KEY.get(style, "F#m")
        degrees = ([x.strip() for x in args.progression.split(",") if x.strip()]
                   if args.progression else default_progression(key))

        if style not in STYLES:
            raise ValueError(f"未知风格 {style!r}：可选 {', '.join(STYLES)}")

        if args.sections and args.duration:
            raise ValueError("--sections 与 --duration 只能给一个")
        if args.duration:
            sections = fit_sections(bpm, args.duration)
        else:
            sections = parse_sections(args.sections)

        parse_key(key)
        resolved, _ = build_progression(key, degrees)
    except (ValueError, NotImplementedError) as exc:
        print(f"[参数错误] {exc.args[0] if exc.args else exc}", file=sys.stderr)
        return 2

    title = args.title or (args.desc[:20].strip() or f"{style} 小样")
    slug = args.slug or style
    project_dir = unique_project_dir(args.root, slug)
    project_name = os.path.basename(project_dir)

    cfg = {
        "bpm": bpm,
        "key": key,
        "seed": 0,
        "progression": degrees,
        "style": style,
        "style_tweaks": {},      # 只对这一首微调风格，例：{"bass": {"velocity": 78}}
        "arrange": {},           # 只对这一首覆盖段落，例：{"chorus": {"drums": "medium"}}
        "time_sig": [4, 4],
        "sections": {name: bars for name, bars in sections},
        "velocity_base": 80,
    }

    os.makedirs(os.path.join(project_dir, "music", "output"), exist_ok=True)

    with open(os.path.join(project_dir, "config.json"), "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

    with open(os.path.join(project_dir, "brief.md"), "w", encoding="utf-8") as f:
        f.write(build_brief(title, args.desc, cfg, sections, resolved, project_name))

    with open(os.path.join(project_dir, "decisions.md"), "w", encoding="utf-8") as f:
        f.write(
            f"# decisions.md — {title}\n\n"
            f"每个有听感后果的改动记一条：改了什么 / 为什么 / 预期听到什么变化。\n\n"
            f"## v1 — {datetime.date.today().isoformat()}（初始生成）\n\n"
            f"- 描述：{args.desc or '（无）'}\n"
            f"- 风格 {style} / 调性 {key} / {bpm}bpm / 和弦 {' - '.join(resolved)}\n"
            f"- 段落：{'，'.join(f'{n}{b}小节' for n, b in sections)}\n"
        )

    # 推断过程如实打印，方便覆盖
    if hits:
        best = hits[0]
        guessed = []
        if not args.style:
            guessed.append(f"风格={best[1]}")
        if not args.bpm:
            guessed.append(f"bpm={best[0]}")
        if guessed:
            print(f"[推断] 命中「{best[2]}」-> {' / '.join(guessed)}（可覆盖）")
        else:
            print(f"[推断] 命中「{best[2]}」，但风格与 bpm 已显式指定，按你的来")

        others = [h for h in hits[1:] if h[1] != best[1] and h[1] != style]
        if others:
            alt = "、".join(f"{h[1]}（{h[2]}）" for h in others)
            print(f"[提示] 描述里还命中 {alt}，当前按 {style} 生成；想换加 --style <名字>")
    else:
        print("[推断] 描述里没识别到风格关键词，使用默认 cinematic / 84bpm")

    if not args.key:
        print(f"[推断] 调性未指定，按风格给 {key}（调性不猜情绪，要别的加 --key）")

    print(f"\n项目已建立: {project_dir}")
    print(f"  风格 {style}  调性 {key}  和弦 {' - '.join(resolved)}")
    print(f"  段落 {' / '.join(f'{n}:{b}' for n, b in sections)}"
          f"（共 {sum(b for _, b in sections)} 小节）")
    print("\n下一步:")
    print(f"  bash tools/compose.sh {os.path.relpath(project_dir, _ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
