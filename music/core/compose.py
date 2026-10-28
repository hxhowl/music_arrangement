import argparse
import json
import os
import random
import re
import sys

import pretty_midi

# ===== 路径修复：把 music/ 加入 sys.path =====
_MUSIC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _MUSIC_DIR not in sys.path:
    sys.path.insert(0, _MUSIC_DIR)

from core.arrange import TRACK_KEYS, get as get_arrange
from core.config import load_config
from core.context import Ctx
from core.report import check
from core.styles import resolve as resolve_style
from core.theory import build_progression
from patterns.bass import build as build_bass
from patterns.chords import build as build_chords
from patterns.drums import build as build_drums
from patterns.lead import build as build_lead
from patterns.pad import build as build_pad

# 与 Logic Pro 默认 PPQ 对齐，避免 16 分/三连音导入时被重新量化
RESOLUTION = 960

# 轨定义：program 只是 GM 音色兜底，真实音色在 Logic 里换
TRACKS = {
    "chords": dict(program=0,  name="chords"),
    "bass":   dict(program=33, name="bass"),
    "drums":  dict(program=0,  name="drums", is_drum=True),
    "lead":   dict(program=80, name="lead"),
    "pad":    dict(program=90, name="pad"),
}

assert set(TRACKS) == set(TRACK_KEYS), "compose.TRACKS 与 arrange.TRACK_KEYS 不一致"


def _version_plan(version: str, takes: int, base_seed: int):
    """算出这一批要出哪些版本、各用什么 seed。

    takes>1 时：版本号 vN..vN+k-1，seed 从 config 的 seed 递增 ——
    每版都是同一编曲的不同演奏（seed=0 时就是 1..k）。
    """
    if takes <= 1:
        return [(version, base_seed)]

    matched = re.fullmatch(r"v(\d+)", version)
    if not matched:
        raise ValueError(f"--takes 需要形如 v3 的版本号，收到 {version!r}")

    start = int(matched.group(1))
    return [(f"v{start + i}", base_seed + i + 1) for i in range(takes)]


def compose(project_dir: str, version: str = "v1", report: bool = True,
            seed: int = None, takes: int = 1):
    """生成一版或 N 版，返回 [(路径, 体检是否通过), ...]。"""
    cfg = load_config(project_dir)
    if seed is not None:
        if not isinstance(seed, int) or seed < 0:
            raise ValueError(f"seed={seed!r} 必须是非负整数")
        cfg["seed"] = seed

    results = []
    for take_version, take_seed in _version_plan(version, takes, cfg.get("seed", 0)):
        results.append(_render(project_dir, cfg, take_version, take_seed, report))
    return results


def _render(project_dir: str, cfg: dict, version: str, seed: int, report: bool):
    bpm = cfg["bpm"]
    num, den = cfg["time_sig"]
    style = cfg["style"]

    # 风格 + 项目内微调；arrange + 项目内覆盖。都不碰全局文件
    style_spec = resolve_style(style, cfg.get("style_tweaks"))
    arrange_overrides = cfg.get("arrange")

    # 级数 -> 实际和弦
    progression, chord_map = build_progression(cfg["key"], cfg["progression"])

    # seed=0 时 rng 为 None，产物完全确定（同参数两次生成字节相同）
    rng = random.Random(seed) if seed else None

    pm = pretty_midi.PrettyMIDI(initial_tempo=bpm, resolution=RESOLUTION)
    pm.time_signature_changes.append(pretty_midi.TimeSignature(num, den, 0))

    insts = {key: pretty_midi.Instrument(**kw) for key, kw in TRACKS.items()}

    # 主控力度：velocity_base 80 为基准，整体等比缩放
    master = cfg.get("velocity_base", 80) / 80.0

    bar = 0
    for section, bars in cfg["sections"].items():
        arr = get_arrange(section, arrange_overrides)
        ctx = Ctx(
            bpm=bpm,
            start_bar=bar,
            bars=bars,
            progression=progression,
            chords=chord_map,
            vel_scale=arr["vel"] * master,
            style=style,
            style_spec=style_spec,
            density=arr["drums"],
            crash=(section == "chorus"),   # 副歌进吊镲
            fill=(section != "outro"),     # 收尾段不再加过门
            seed=seed,
            rng=rng,
        )

        if arr["chords"]:
            build_chords(insts["chords"], ctx)
        if arr["bass"]:
            build_bass(insts["bass"], ctx)
        if arr["drums"]:
            build_drums(insts["drums"], ctx)
        if arr["lead"]:
            build_lead(insts["lead"], ctx)
        if arr["pad"]:
            build_pad(insts["pad"], ctx)

        bar += bars

    # 没有音符的轨直接丢掉，别在 Logic 里留一条空白轨
    pm.instruments = [insts[key] for key in TRACK_KEYS if insts[key].notes]

    out_dir = os.path.join(project_dir, "music", "output")
    os.makedirs(out_dir, exist_ok=True)
    project_name = os.path.basename(os.path.normpath(project_dir))
    out_file = os.path.join(out_dir, f"{project_name}-{version}.mid")
    pm.write(out_file)

    # 参数快照：保证这一版永久可复现（含实际使用的 seed）
    snapshot = os.path.join(out_dir, f"{project_name}-{version}.config.json")
    saved = dict(cfg)
    saved["seed"] = seed
    with open(snapshot, "w", encoding="utf-8") as f:
        json.dump(saved, f, ensure_ascii=False, indent=2)

    print(f"生成完成: {out_file}")
    print(f"参数快照: {snapshot}")
    print(f"[info] 风格={style}  调性={cfg['key']}  和弦={' - '.join(progression)}"
          f"  seed={seed}" + ("（完全确定）" if seed == 0 else "（随机演奏）"))

    ok = True
    if report:
        ok = check(out_file, saved, progression=progression)
    return out_file, ok


def main(argv=None):
    parser = argparse.ArgumentParser(description="按项目 config 生成多轨 MIDI")
    parser.add_argument("--project", default="projects/demo")
    parser.add_argument("--version", default="v1")
    parser.add_argument("--seed", type=int, default=None,
                        help="覆盖 config 里的 seed：0=完全确定，>0=随机演奏（挑版本就换 seed）")
    parser.add_argument("--takes", type=int, default=1,
                        help="一次出 N 版（seed 1..N，版本号依次递增）")
    parser.add_argument("--no-report", action="store_true", help="跳过产物体检")
    args = parser.parse_args(argv)

    if args.seed is not None and args.takes > 1:
        parser.error("--seed 与 --takes 不能同时用：--takes 会自己分配 seed 1..N")
    if args.takes < 1:
        parser.error("--takes 至少为 1")

    try:
        results = compose(args.project, args.version, report=not args.no_report,
                          seed=args.seed, takes=args.takes)
    except (KeyError, ValueError, NotImplementedError, FileNotFoundError) as exc:
        # 配置/编排错误不甩 traceback，直接给一句能照着改的话
        message = exc.args[0] if exc.args else str(exc)
        print(f"[配置错误] {message}", file=sys.stderr)
        return 2

    if len(results) > 1:
        print(f"\n共生成 {len(results)} 版：")
        for path, ok in results:
            print(f"  {'✓' if ok else '✗'} {os.path.basename(path)}")

    return 0 if all(ok for _, ok in results) else 1


if __name__ == "__main__":
    sys.exit(main())
