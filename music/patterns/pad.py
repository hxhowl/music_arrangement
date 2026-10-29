import pretty_midi

from core.theory import chord_root_pitch, scale_velocity


def build(pad_inst, ctx):
    """铺底长音。

    音区与旋律重叠是正常的（真实乐器音域本来就大量重叠），真正要避免的是
    **同一时刻响同一个音高** —— 那会让旋律失去轮廓（同频叠置会互相抵消）。
    所以这里做三件事：
      1) 跳过本小节里主旋律已经占用的音高（少一个音也比糊掉好）
      2) 有旋律的段落把 pad 压低一点，给它让位
      3) 按和声节奏分块，半小节换和弦时重新起音，不会一直吊在旧和弦上
    """
    spec = ctx.style_spec["pad"]
    duck = float(spec.get("duck", 1.0)) if ctx.lead_playing else 1.0
    velocity = scale_velocity(spec["velocity"], ctx.vel_scale) * duck
    hold = float(spec.get("hold", 1.0))
    beat = ctx.beat

    for i in range(ctx.bars):
        for offset, span_beats, name in ctx.chord_spans(i):
            root = chord_root_pitch(name, spec["octave"])
            start = ctx.at(i, offset)
            end = start + span_beats * beat * hold

            pitches = [root + semi for semi in spec["intervals"]]
            kept = [p for p in pitches if not ctx.is_occupied(i, p)]

            # 全被占了就留最低的那个，避免这一段彻底没有和声
            if not kept and pitches:
                kept = [min(pitches)]

            for pitch in kept:
                pad_inst.notes.append(
                    pretty_midi.Note(
                        velocity=max(1, int(velocity)),
                        pitch=pitch,
                        start=start,
                        end=end,
                    )
                )
