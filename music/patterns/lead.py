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
    """主旋律：按和弦音级取音，逐音跟随和声节奏。

    旧版每小节算一次音级表，半小节换和弦时后半小节会踩在旧和弦上。
    现在每个音用它自己所在拍位的和弦 —— 换和弦的那一刻旋律自动跟着走。
    """
    spec = ctx.style_spec["lead"]
    phrases = spec["phrases"]
    breath_every = spec["breath_every"]
    breath = spec["breath"]
    target = spec["target"]
    low, high = spec["range"]
    beat = ctx.beat

    # seed 只换"从哪一句开始"，不改变句子本身，所以还是同一套风格的不同演奏
    offset = (ctx.seed % len(phrases)) if ctx.seed else 0
    # 上一个音作为下一个音的"就近目标"，让旋律自身也连贯
    last_pitch = None

    for i in range(ctx.bars):
        plan = breath if (breath_every and i % breath_every == breath_every - 1) \
            else phrases[(i // 2 + offset) % len(phrases)]

        for degree, offset_beats, beats in plan:
            name = ctx.chord_at_beat(i, offset_beats)
            anchor = _anchor(
                name, ctx.chords[name], last_pitch if last_pitch is not None else target,
                low, high,
            )
            tones = _chord_tones(name, ctx.chords[name], anchor, TONE_COUNT, high)

            pitch = tones[min(degree, len(tones) - 1)]
            while pitch > high:
                pitch -= 12
            while pitch < low:
                pitch += 12

            # 旋律音可以跨过换和弦的位置（长音压过和声变化是正常写法），不切
            start = ctx.sway(ctx.at(i, offset_beats))
            end = start + beats * beat

            lead_inst.notes.append(
                pretty_midi.Note(
                    velocity=ctx.jitter(scale_velocity(spec["velocity"], ctx.vel_scale)),
                    pitch=pitch,
                    start=start,
                    end=max(end, start + 0.05),
                )
            )
            last_pitch = pitch
            # 登记本小节旋律占用的音高，让 pad / arp 之类的声部避开
            ctx.occupy(i, [pitch])
            ctx.register_lead(start, end, pitch)
