"""版本差异：这一版和上一版比，到底变了什么。

体检只回答"这版有没有错"，不回答"这版改了什么"。换风格、调参数之后，
人肉 diff 两个 .mid 不现实，所以这里给一行摘要：哪条轨多了/少了几个音、音域动了没有。

只做**结构层面**的对比（音符数 / 音域 / 轨的增删），不做音高逐音比对 ——
后者噪声太大，看的人也不会读。
"""

import os
import re


def _snapshot(instruments):
    """{轨名: (音符数, 最低音, 最高音)}"""
    snap = {}
    for inst in instruments:
        pitches = [n.pitch for n in inst.notes]
        if not pitches:
            continue
        snap[inst.name] = (len(pitches), min(pitches), max(pitches))
    return snap


def _name(pitch: int) -> str:
    try:
        import pretty_midi

        return pretty_midi.note_number_to_name(pitch)
    except Exception:
        return str(pitch)


def previous_version(out_dir: str, project_name: str, version: str):
    """找比 version 小的最大版本号（如 v9 的上一版是 v8）。没有就返回 None。"""
    matched = re.fullmatch(r"v(\d+)", version or "")
    if not matched:
        return None
    current = int(matched.group(1))

    best, best_num = None, -1
    for filename in os.listdir(out_dir):
        found = re.fullmatch(re.escape(project_name) + r"-(v\d+)\.mid", filename)
        if not found:
            continue
        number = int(found.group(1)[1:])
        if number < current and number > best_num:
            best, best_num = found.group(1), number
    return best


def describe(prev_mid: str, instruments) -> list:
    """对比上一版与本版，返回若干条人话摘要（空列表 = 没有变化）。"""
    import pretty_midi

    try:
        before = _snapshot(pretty_midi.PrettyMIDI(prev_mid).instruments)
    except Exception:
        return []

    after = _snapshot(instruments)
    lines = []

    for name in sorted(set(after) - set(before)):
        lines.append(f"新增轨 `{name}`（{after[name][0]} 音）")
    for name in sorted(set(before) - set(after)):
        lines.append(f"少了轨 `{name}`（原本 {before[name][0]} 音）")

    for name in sorted(set(before) & set(after)):
        old_count, old_lo, old_hi = before[name]
        new_count, new_lo, new_hi = after[name]
        parts = []
        if old_count != new_count:
            parts.append(f"{old_count}→{new_count} 音")
        if (old_lo, old_hi) != (new_lo, new_hi):
            parts.append(
                f"音域 {_name(old_lo)}~{_name(old_hi)}→{_name(new_lo)}~{_name(new_hi)}"
            )
        if parts:
            lines.append(f"`{name}` " + "，".join(parts))

    return lines
