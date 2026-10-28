"""产物体检：不开 Logic 也能发现空轨、段落空白、小节数不符、PPQ 不对等问题。

用法:
    python music/core/report.py <file.mid> [--project projects/demo]
或:
    bash tools/check.sh projects/demo/music/output/demo-v3.mid projects/demo
"""

import argparse
import os
import sys

import mido
import pretty_midi

_MUSIC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _MUSIC_DIR not in sys.path:
    sys.path.insert(0, _MUSIC_DIR)

EXPECTED_PPQ = 960

# 各轨建议音域（MIDI 音高）。超出只提示，不判失败 —— 有时是刻意的。
ROLE_RANGE = {
    "chords": (40, 72),
    "bass":   (28, 50),
    "pad":    (50, 88),
    "lead":   (56, 92),
    "drums":  (35, 60),
}


def _last_active_bar(sections) -> dict:
    """每个轨按编排应在第几小节结束 —— 用于区分「该收的留白」和「意外断掉」。"""
    from core.arrange import TRACK_KEYS, get

    out = {}
    offset = 0
    for section, count in sections.items():
        arr = get(section)
        for key in TRACK_KEYS:
            if arr.get(key):
                out[key] = offset + count
        offset += count
    return out


def check(mid_path: str, config: dict = None) -> bool:
    """检查一份 MIDI 产物，返回是否通过（问题会打印出来）。"""
    issues = []
    hints = []

    m = mido.MidiFile(mid_path)
    if m.type != 1:
        issues.append(f"format={m.type}，应为 1（多轨分离）")
    if m.ticks_per_beat != EXPECTED_PPQ:
        issues.append(f"PPQ={m.ticks_per_beat}，应为 {EXPECTED_PPQ}（与 Logic 默认对齐）")

    pm = pretty_midi.PrettyMIDI(mid_path)
    tempi = pm.get_tempo_changes()
    bpm = float(tempi[1][0]) if len(tempi[1]) else 120.0
    bar_len = 4 * (60.0 / bpm)
    end = pm.get_end_time()
    bars = end / bar_len

    print(f"\n产物: {os.path.basename(mid_path)}")
    print(f"  format={m.type}  PPQ={m.ticks_per_beat}  BPM={bpm:.1f}  "
          f"时长 {end:.1f}s = {bars:.2f} 小节  轨数={len(pm.instruments)}")

    print(f"\n  轨        音符   音域        力度      至(小节)")
    expected_last = _last_active_bar(config["sections"]) if config else {}
    for inst in pm.instruments:
        pitches = [n.pitch for n in inst.notes]
        if not pitches:
            print(f"  {inst.name:<8}  0     —")
            issues.append(f"轨 {inst.name!r} 没有音符")
            continue

        vels = [n.velocity for n in inst.notes]
        lo, hi = min(pitches), max(pitches)
        rng = f"{pretty_midi.note_number_to_name(lo)}~{pretty_midi.note_number_to_name(hi)}"
        last_bar = max(n.end for n in inst.notes) / bar_len
        print(f"  {inst.name:<8}  {len(pitches):>3}    {rng:<10}  "
              f"{min(vels)}~{max(vels):<6}  {last_bar:>6.2f}")

        low, high = ROLE_RANGE.get(inst.name, (0, 127))
        if not (low <= lo and hi <= high):
            hints.append(f"轨 {inst.name!r} 音域 {rng} 超出建议 {low}~{high}")

        # 只有「按编排本该还在响」的轨提前收声才提示，避免把设计好的留白报成问题
        # 容差 2 小节：段落末尾留白（如 lead 每两小节才写一次）不算异常
        due = expected_last.get(inst.name, bars)
        if bars - last_bar > 2 and last_bar < due - 2:
            hints.append(
                f"轨 {inst.name!r} 在 {last_bar:.1f} 小节后就没音了"
                f"（按编排应到 {due} 小节）"
            )

    # 鼓必须落在 channel 10（0-index 9）
    for track in m.tracks:
        name = next((msg.name for msg in track if msg.type == "track_name"), "")
        if name.strip().lower() != "drums":
            continue
        channels = {
            msg.channel for msg in track
            if msg.type in ("note_on", "note_off") and getattr(msg, "velocity", 1) != 0
        }
        if channels and channels != {9}:
            issues.append(f"鼓轨落在 channel {sorted(c + 1 for c in channels)}，应为 10")

    if config:
        cfg_bpm = float(config["bpm"])
        if abs(bpm - cfg_bpm) > 0.5:
            issues.append(f"文件 BPM={bpm:.1f} 与 config bpm={cfg_bpm:g} 不符")

        expected = sum(int(v) for v in config["sections"].values())
        if abs(bars - expected) > 0.05:
            issues.append(f"实际 {bars:.2f} 小节 ≠ config 声明 {expected} 小节")

        # 逐段检查是否真有音 —— 旧的 if 白名单把 outro 整段丢掉了，这条能直接抓到
        starts = sorted(n.start for inst in pm.instruments for n in inst.notes)
        offset = 0
        for section, count in config["sections"].items():
            lo, hi = offset * bar_len, (offset + count) * bar_len
            if not any(lo <= s < hi for s in starts):
                issues.append(
                    f"段落 {section!r}（第 {offset + 1}~{offset + count} 小节）没有任何音符"
                )
            offset += count

        from core.arrange import active_tracks
        expected_tracks = active_tracks(config["sections"])
        actual = {inst.name for inst in pm.instruments if inst.notes}
        missing = expected_tracks - actual
        if missing:
            issues.append(f"以下轨按编排应有音符但实际为空: {sorted(missing)}")

    for hint in hints:
        print(f"  [提示] {hint}")

    if issues:
        print("\n  [失败] 体检未通过:")
        for issue in issues:
            print(f"    - {issue}")
        return False

    print("\n  [通过] 体检通过")
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description="MIDI 产物体检")
    parser.add_argument("mid", help="要检查的 .mid 文件")
    parser.add_argument("--project", default=None, help="项目目录，用于读取 config.json 做对照")
    args = parser.parse_args(argv)

    config = None
    if args.project:
        from core.config import load_config
        config = load_config(args.project)

    return 0 if check(args.mid, config) else 1


if __name__ == "__main__":
    sys.exit(main())
