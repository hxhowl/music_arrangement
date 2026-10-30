import pretty_midi

from core.theory import chord_root_pitch, scale_velocity


def _bar_of(ctx, seconds: float, start_bar: int) -> int:
    """某个绝对时间点落在段内第几小节（夹在本段范围内）。"""
    if not ctx.bar_len:
        return start_bar
    index = int(((seconds - 1e-6) - ctx.bar_time(0)) // ctx.bar_len)
    return max(start_bar, min(ctx.bars - 1, index))


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

            # 这个 pad 音会盖住哪几小节：和弦跨两小节时它只查起始小节，
            # 第二小节里的旋律就撞上了（体检会报"同音高同时发声"）
            last_bar = _bar_of(ctx, end, i)

            pitches = [root + semi for semi in spec["intervals"]]
            kept = [
                p for p in pitches
                if not any(ctx.is_occupied(b, p) for b in range(i, last_bar + 1))
            ]

            # 全被占了就这一拍不出 pad —— 那些音高主旋律已经在响了，
            # 和声没有丢；硬塞一个反而变成同度叠置（体检会报"同音高同时发声"）
            if not kept:
                continue

            for pitch in kept:
                pad_inst.notes.append(
                    pretty_midi.Note(
                        velocity=max(1, int(velocity)),
                        pitch=pitch,
                        start=start,
                        end=end,
                    )
                )
