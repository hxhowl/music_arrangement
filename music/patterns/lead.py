import pretty_midi

from core.theory import chord_root_pitch, scale_velocity

LOW, HIGH = 60, 83

# 呼吸小节：只留两个长音，给 4 小节乐句一个停顿
BREATH = ((0, 0.0, 1.8), (2, 2.0, 1.8))


def _pitch_classes(chord_name: str, semitones) -> set:
    root_pc = chord_root_pitch(chord_name, 0) % 12
    return {(root_pc + semi) % 12 for semi in semitones}


def _anchor(chord_name: str, semitones, target: int) -> int:
    """在 LOW~HIGH 内挑离 target 最近的和弦内音，保证起手音永远落在和弦上。"""
    pcs = _pitch_classes(chord_name, semitones)
    candidates = [p for p in range(LOW, HIGH + 1) if p % 12 in pcs]
    return min(candidates, key=lambda p: (abs(p - target), p))


def _chord_tones(chord_name: str, semitones, start: int, count: int) -> list:
    """从 start 起向上取 count 个和弦内音，供动机按音级索引。"""
    pcs = _pitch_classes(chord_name, semitones)
    tones = []
    pitch = start
    while len(tones) < count and pitch <= HIGH + 12:
        if pitch % 12 in pcs:
            tones.append(pitch)
        pitch += 1
    return tones


def build(lead_inst, ctx):
    spec = ctx.style_spec["lead"]
    phrases = spec["phrases"]
    breath_every = spec.get("breath_every", 0)
    target = spec.get("target", 69)
    beat = ctx.beat

    # seed 只换"从哪一句开始"，不改变句子本身，所以还是同一套风格的不同演奏
    offset = (ctx.seed % len(phrases)) if ctx.seed else 0

    for i in range(ctx.bars):
        name = ctx.chord_at(i)

        if breath_every and i % breath_every == breath_every - 1:
            plan = BREATH
        else:
            plan = phrases[(i // 2 + offset) % len(phrases)]

        tones = _chord_tones(
            name, ctx.chords[name], _anchor(name, ctx.chords[name], target), 4
        )
        start = ctx.bar_time(i)

        for degree, offset_beats, beats in plan:
            pitch = tones[degree]
            while pitch > HIGH:
                pitch -= 12
            lead_inst.notes.append(
                pretty_midi.Note(
                    velocity=ctx.jitter(scale_velocity(84, ctx.vel_scale), 3),
                    pitch=pitch,
                    start=ctx.sway(start + offset_beats * beat),
                    end=start + (offset_beats + beats) * beat,
                )
            )
