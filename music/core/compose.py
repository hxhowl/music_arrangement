import argparse
import json
import os
import sys

import pretty_midi

# ===== 路径修复：把 music/ 加入 sys.path =====
_MUSIC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _MUSIC_DIR not in sys.path:
    sys.path.insert(0, _MUSIC_DIR)

from core.arrange import TRACK_KEYS, get as get_arrange
from core.config import load_config
from core.report import check
from core.theory import PROGRESSION
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


def compose(project_dir: str, version: str = "v1", report: bool = True):
    """按项目 config + 编排矩阵生成 MIDI，并写一份参数快照。

    返回 (产物路径, 体检是否通过)。
    """
    cfg = load_config(project_dir)
    bpm = cfg["bpm"]
    num, den = cfg["time_sig"]

    pm = pretty_midi.PrettyMIDI(initial_tempo=bpm, resolution=RESOLUTION)
    pm.time_signature_changes.append(pretty_midi.TimeSignature(num, den, 0))

    insts = {key: pretty_midi.Instrument(**kw) for key, kw in TRACKS.items()}

    # 主控力度：velocity_base 80 为基准，整体等比缩放
    master = cfg.get("velocity_base", 80) / 80.0

    bar = 0
    for section, bars in cfg["sections"].items():
        arr = get_arrange(section)
        vs = arr["vel"] * master

        if arr["chords"]:
            build_chords(insts["chords"], bpm, bar, bars, vel_scale=vs)
        if arr["bass"]:
            build_bass(insts["bass"], bpm, bar, bars, vel_scale=vs)
        if arr["drums"]:
            build_drums(
                insts["drums"], bpm, bar, bars,
                density=arr["drums"],
                vel_scale=vs,
                crash=(section == "chorus"),   # 副歌进吊镲
                fill=(section != "outro"),     # 收尾段不再加过门
            )
        if arr["lead"]:
            build_lead(insts["lead"], bpm, bar, bars, vel_scale=vs)
        if arr["pad"]:
            build_pad(insts["pad"], bpm, bar, bars, vel_scale=vs)

        bar += bars

    # 没有音符的轨直接丢掉，别在 Logic 里留一条空白轨
    pm.instruments = [insts[key] for key in TRACK_KEYS if insts[key].notes]

    out_dir = os.path.join(project_dir, "music", "output")
    os.makedirs(out_dir, exist_ok=True)
    project_name = os.path.basename(os.path.normpath(project_dir))
    out_file = os.path.join(out_dir, f"{project_name}-{version}.mid")
    pm.write(out_file)

    # 参数快照：保证这一版永久可复现（改 config 也不影响已出的版本）
    snapshot = os.path.join(out_dir, f"{project_name}-{version}.config.json")
    with open(snapshot, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

    print(f"生成完成: {out_file}")
    print(f"参数快照: {snapshot}")
    print(f"[info] 和弦进行 {'-'.join(PROGRESSION)}（config 的 key={cfg['key']} 仅作记录，不参与生成）")

    ok = True
    if report:
        ok = check(out_file, cfg)
    return out_file, ok


def main(argv=None):
    parser = argparse.ArgumentParser(description="按项目 config 生成多轨 MIDI")
    parser.add_argument("--project", default="projects/demo")
    parser.add_argument("--version", default="v1")
    parser.add_argument("--no-report", action="store_true", help="跳过产物体检")
    args = parser.parse_args(argv)

    try:
        _, ok = compose(args.project, args.version, report=not args.no_report)
    except (KeyError, ValueError, NotImplementedError, FileNotFoundError) as exc:
        # 配置/编排错误不甩 traceback，直接给一句能照着改的话
        message = exc.args[0] if exc.args else str(exc)
        print(f"[配置错误] {message}", file=sys.stderr)
        return 2

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
