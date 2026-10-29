import pretty_midi

from core.theory import chord_root_pitch, scale_velocity

TONE_COUNT = 4


def _tones(name: str, semitones, low: int, high: int, target: int):
    """在 low~high 内从离 target 最近的和弦音起，向上取 4 个音级。"""
    root_pc = chord_root_pitch(name, 0) % 12
    pcs = {(root_pc + semi) % 12 for semi in semitones}
    inside = [p for p in range(low, high + 1) if p % 12 in pcs]
    if not inside:
        return []
    anchor = min(inside, key=lambda p: (abs(p - target), p))

    tones = []
    pitch = anchor
    while len(tones) < TONE_COUNT and pitch <= high + 12:
        if pitch % 12 in pcs:
            tones.append(pitch)
        pitch += 1
    return tones


def build(counter_inst, ctx):
    """副旋律：在**主旋律空着的地方**补一条低音区的答句。

    设计原则（这几条决定了它是"副旋律"而不是"第二条主旋律"）：
      1) 只在 lead 没响的时候写 —— 两条线同时抢注意力就不叫 counter 了
      2) 音区压在 lead 之下，听觉上像"回话"而不是"抢话"
      3) 用和弦音级取音，音高由"离上一个音最近"决定，保持自己的连贯
      4) 落到 lead 正在响的音高上就整颗丢掉 —— 同音叠置会把旋律轮廓磨平
    """
    spec = ctx.style_spec["counter"]
    low, high = spec["range"]
    target = spec.get("target", (low + high) // 2)
    beat = ctx.beat
    last_pitch = None

    for i in range(ctx.bars):
        for offset, beats, degree in spec["rhythm"]:
            start = ctx.at(i, offset)
            end = start + beats * beat

            if ctx.lead_sounding(start, end):
                continue

            name = ctx.chord_at_beat(i, offset)
            tones = _tones(
                name, ctx.chords[name], low, high,
                last_pitch if last_pitch is not None else target,
            )
            if not tones:
                continue

            pitch = tones[min(degree, len(tones) - 1)]
            while pitch > high:
                pitch -= 12
            while pitch < low:
                pitch += 12

            # 与主旋律同音高同时又响：直接放弃这一颗
            if any(p == pitch and s < end - 1e-6 and start < e - 1e-6
                   for s, e, p in ctx.lead_notes):
                continue

            counter_inst.notes.append(
                pretty_midi.Note(
                    velocity=ctx.jitter(
                        scale_velocity(spec["velocity"], ctx.vel_scale)
                    ),
                    pitch=pitch,
                    start=ctx.sway(start),
                    end=end,
                )
            )
            last_pitch = pitch
            # 登记占用，让后面构建的 pad 让开（同音叠置会让副旋律的轮廓变模糊）
            ctx.occupy(i, [pitch])
