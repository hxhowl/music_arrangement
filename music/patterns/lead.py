import pretty_midi

from core.theory import chord_root_pitch, scale_velocity

# 旋律最多按「和弦内第 4 个音」取音（根-三-五-八），够用且不会跑出音区
TONE_COUNT = 4


def _pitch_classes(chord_name: str, semitones) -> set:
    root_pc = chord_root_pitch(chord_name, 0) % 12
    return {(root_pc + semi) % 12 for semi in semitones}


def _anchor(chord_name: str, semitones, target: int, low: int, high: int) -> int:
    """在 low~high 内挑离 target 最近的和弦内音，保证起手音永远落在和弦上。"""
    pcs = _pitch_classes(chord_name, semitones)
    candidates = [p for p in range(low, high + 1) if p % 12 in pcs]
    if not candidates:
        raise ValueError(f"旋律音区 {low}~{high} 太窄，放不下 {chord_name} 的和弦音")
    return min(candidates, key=lambda p: (abs(p - target), p))


def _chord_tones(chord_name: str, semitones, start: int, count: int, high: int) -> list:
    """从 start 起向上取 count 个和弦内音，供动机按音级索引。"""
    pcs = _pitch_classes(chord_name, semitones)
    tones = []
    pitch = start
    while len(tones) < count and pitch <= high + 12:
        if pitch % 12 in pcs:
            tones.append(pitch)
        pitch += 1
    return tones


def build(lead_inst, ctx):
    spec = ctx.style_spec["lead"]
    phrases = spec["phrases"]
    breath_every = spec["breath_every"]
    breath = spec["breath"]
    target = spec["target"]
    low, high = spec["range"]
    beat = ctx.beat

    # seed 只换"从哪一句开始"，不改变句子本身，所以还是同一套风格的不同演奏
    offset = (ctx.seed % len(phrases)) if ctx.seed else 0

    for i in range(ctx.bars):
        name = ctx.chord_at(i)

        if breath_every and i % breath_every == breath_every - 1:
            plan = breath
        else:
            plan = phrases[(i // 2 + offset) % len(phrases)]

        tones = _chord_tones(
            name, ctx.chords[name], _anchor(name, ctx.chords[name], target, low, high),
            TONE_COUNT, high,
        )
        start = ctx.bar_time(i)
        played = []

        for degree, offset_beats, beats in plan:
            pitch = tones[degree]
            while pitch > high:
                pitch -= 12
            played.append(pitch)
            lead_inst.notes.append(
                pretty_midi.Note(
                    velocity=ctx.jitter(scale_velocity(spec["velocity"], ctx.vel_scale)),
                    pitch=pitch,
                    start=ctx.sway(start + offset_beats * beat),
                    end=start + (offset_beats + beats) * beat,
                )
            )

        # 登记本小节旋律占用的音高，让 pad 之类的铺底声部避开
        ctx.occupy(i, played)
