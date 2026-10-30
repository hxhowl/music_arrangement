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
from core.cues import write_cues
from core.diff import describe as describe_changes
from core.diff import previous_version
from core.index import write as write_index
from core.instruments import describe as describe_instruments
from core.instruments import merge_tweaks, plan as plan_instruments, tweaks_of
from core.report import check
from core.styles import resolve as resolve_style
from core.theory import build_progression
from patterns.arp import build as build_arp
from patterns.bass import build as build_bass
from patterns.chords import build as build_chords
from patterns.counter import build as build_counter
from patterns.drums import build as build_drums
from patterns.lead import build as build_lead
from patterns.pad import build as build_pad
from patterns.perc import build as build_perc

# 与 Logic Pro 默认 PPQ 对齐，避免 16 分/三连音导入时被重新量化
RESOLUTION = 960

# 轨属性：名字 + 是否鼓。**program 不在这里** —— 它由乐器选择决定
# （core/instruments.py 的 plan()），这样"换乐器"只有一处来源。
TRACKS = {
    "chords":  dict(name="chords"),
    "bass":    dict(name="bass"),
    "drums":   dict(name="drums", is_drum=True),
    "perc":    dict(name="perc", is_drum=True),
    "arp":     dict(name="arp"),
    "lead":    dict(name="lead"),
    "counter": dict(name="counter"),
    "pad":     dict(name="pad"),
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

    # 排练段落覆盖；风格在下面按段解析（每段可能用不同 style）
    arrange_overrides = cfg.get("arrange") or {}

    unused = set(arrange_overrides) - set(cfg["sections"])
    if unused:
        print(f"[warn] config.arrange 里的 {sorted(unused)} 不在 sections 里，本次不会生效")

    # 级数 -> 实际和弦。是否用七和弦由风格决定，所以按 seventh 缓存两套
    prog_cache = {}

    def progression_for(seven: bool):
        if seven not in prog_cache:
            prog_cache[seven] = build_progression(
                cfg["key"], cfg["progression"], seventh=seven
            )
        return prog_cache[seven]

    progression, _ = progression_for(False)

    # seed=0 时 rng 为 None，产物完全确定（同参数两次生成字节相同）
    rng = random.Random(seed) if seed else None

    pm = pretty_midi.PrettyMIDI(initial_tempo=bpm, resolution=RESOLUTION)
    pm.time_signature_changes.append(pretty_midi.TimeSignature(num, den, 0))

    # 每个功能槽用什么乐器：DEFAULT < preset < config.instruments
    plan_map = plan_instruments(cfg)

    insts = {
        key: pretty_midi.Instrument(program=plan_map[key]["program"], **kw)
        for key, kw in TRACKS.items()
    }

    # 主控力度：velocity_base 80 为基准，整体等比缩放
    master = cfg.get("velocity_base", 80) / 80.0
    # 全曲统一的拍感参数（不跟风格走：swing 是"这首歌怎么摇"，不是"这套风格怎么打"）
    swing = float(cfg.get("swing", 0.0) or 0.0)
    harmonic_rhythm = cfg.get("harmonic_rhythm")

    # 段落可以各自指定 style；同一个 style 只解析一次
    # 演奏法微调：乐器自带的最低，config.style_tweaks 优先
    tweaks = merge_tweaks(cfg.get("style_tweaks"), tweaks_of(plan_map))
    spec_cache = {style: resolve_style(style, tweaks)}
    used_sections = {}

    # 主旋律占用的音高，跨段共享（键是**绝对**小节号，见 Ctx.occupy）
    occupied = {}
    # 哪几段把副旋律放到了上方（只用于输出提示，方便确认 config 生效了）
    counter_voices = {}

    bar = 0
    for section, bars in cfg["sections"].items():
        arr = get_arrange(section, arrange_overrides)

        section_style = arr["style"] or style
        if section_style not in spec_cache:
            spec_cache[section_style] = resolve_style(section_style, tweaks)
        if section_style != style:
            used_sections[section] = section_style

        section_spec = spec_cache[section_style]
        section_prog, section_chords = progression_for(
            bool(section_spec["chords"].get("seventh"))
        )

        ctx = Ctx(
            bpm=bpm,
            start_bar=bar,
            bars=bars,
            progression=section_prog,
            chords=section_chords,
            vel_scale=arr["vel"] * master,
            style=section_style,
            style_spec=section_spec,
            density=arr["drums"],
            crash=arr["crash"],
            fill=arr["fill"],
            seed=seed,
            rng=rng,
            occupied=occupied,
            lead_playing=bool(arr["lead"]),
            # 和声节奏：config 显式指定优先，否则用该段风格自己的默认值
            beats_per_chord=harmonic_rhythm or float(section_spec["chords"].get("beats", 4)),
            beats_per_bar=num,
            swing=swing,
            counter_voice=arr.get("counter_voice"),
            build=arr.get("build"),
        )

        if arr["chords"]:
            build_chords(insts["chords"], ctx)
        # drums 先于 bass：bass 要读底鼓落点来咬合（见 patterns/bass.py）
        if arr["drums"]:
            build_drums(insts["drums"], ctx)
        if arr["bass"]:
            build_bass(insts["bass"], ctx)
        # lead 先写：arp 和 pad 都要读它占用的音高来避让
        if arr["lead"]:
            build_lead(insts["lead"], ctx)
        if arr.get("perc"):
            build_perc(insts["perc"], ctx)
        if arr.get("arp"):
            build_arp(insts["arp"], ctx)
        # counter 也要在 lead 之后（要读主旋律的空档），但要在 pad 之前（pad 避让它）
        if arr.get("counter"):
            build_counter(insts["counter"], ctx)
            if arr.get("counter_voice"):
                counter_voices[section] = arr["counter_voice"]
        if arr["pad"]:
            build_pad(insts["pad"], ctx)

        bar += bars

    # 没有音符的轨直接丢掉，别在 Logic 里留一条空白轨
    pm.instruments = [insts[key] for key in TRACK_KEYS if insts[key].notes]

    out_dir = os.path.join(project_dir, "music", "output")
    os.makedirs(out_dir, exist_ok=True)
    project_name = os.path.basename(os.path.normpath(project_dir))
    out_file = os.path.join(out_dir, f"{project_name}-{version}.mid")
    # 显式指定版本号时会覆盖旧版 —— 这是唯一会丢历史的路径，所以要出声
    if os.path.exists(out_file):
        print(f"[提示] 覆盖已存在的 {version}（想保留旧版就换一个版本号）")

    # 这一版和上一版比变了什么（体检只说"有没有错"，不说"改了什么"）
    prev = previous_version(out_dir, project_name, version)
    if prev:
        changes = describe_changes(
            os.path.join(out_dir, f"{project_name}-{prev}.mid"), pm.instruments
        )
        detail = "；".join(changes[:6]) if changes else "音符层面没有变化（只有音色或参数动了）"
        print(f"[diff] 相比 {prev}：{detail}")

    pm.write(out_file)

    # 参数快照：保证这一版永久可复现（含实际使用的 seed）
    snapshot = os.path.join(out_dir, f"{project_name}-{version}.config.json")
    saved = dict(cfg)
    saved["seed"] = seed
    with open(snapshot, "w", encoding="utf-8") as f:
        json.dump(saved, f, ensure_ascii=False, indent=2)

    cue_file = write_cues(saved, out_dir, project_name, version)

    print(f"生成完成: {out_file}")
    print(f"参数快照: {snapshot}")
    print(f"音效清单: {cue_file}")
    print(f"[info] 编制: {describe_instruments(plan_map)}")
    rhythm_note = f"和声节奏={harmonic_rhythm:g}拍/和弦" if harmonic_rhythm \
        else "和声节奏=按风格"
    print(f"[info] 风格={style}  调性={cfg['key']}  和弦={' - '.join(progression)}"
          f"  {rhythm_note}"
          + (f"  swing={swing:g}" if swing else "")
          + f"  seed={seed}" + ("（完全确定）" if seed == 0 else "（随机演奏）"))
    if used_sections:
        detail = "、".join(f"{s}={v}" for s, v in used_sections.items())
        print(f"[info] 段落换风格: {detail}")
    if counter_voices:
        detail = "、".join(f"{s}={v}" for s, v in counter_voices.items())
        print(f"[info] 副旋律声部: {detail}")

    ok = True
    if report:
        ok = check(out_file, saved, progression=progression)

    # 作品索引：projects/ 下的歌不进 git，换窗口就看不出有哪些，所以每次重写一张表
    index_path = write_index(os.path.dirname(os.path.abspath(project_dir)))
    if index_path:
        print(f"作品索引: {index_path}")
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
    except (KeyError, ValueError, TypeError, NotImplementedError, FileNotFoundError) as exc:
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
