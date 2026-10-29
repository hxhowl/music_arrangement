import pretty_midi

from core.theory import chord_root_pitch, scale_velocity


def build(arp_inst, ctx):
    """琶音织体：把当前和弦拆成上下来回的分解和弦。

    作用是在中高频铺一层"动"的东西，把留白填住而不抢旋律。
    和声节奏变化时（半小节换和弦）琶音也跟着换，不会踩在旧和弦上。
    """
    spec = ctx.style_spec["arp"]
    low, high = spec["range"]
    step = float(spec["step"])
    octaves = int(spec.get("octaves", 2))
    beat = ctx.beat
    ceiling = min(high, low + 12 * max(1, octaves))

    for i in range(ctx.bars):
        for offset, span_beats, name in ctx.chord_spans(i):
            root_pc = chord_root_pitch(name, 0) % 12
            pcs = {(root_pc + semi) % 12 for semi in ctx.chords[name]}

            # 避开旋律占用的音高：同音叠置会让旋律轮廓变模糊
            tones = [
                p for p in range(low, ceiling + 1)
                if p % 12 in pcs and not ctx.is_occupied(i, p)
            ]
            if not tones:
                continue

            # 上行再下行，比纯上行耐听，也不容易和旋律撞在同一个方向上
            sequence = tones + tones[-2:0:-1] if len(tones) > 2 else tones
            steps = max(1, int(round(span_beats / step)))

            for index in range(steps):
                accent = 1.0 if index % 2 == 0 else 0.8
                when = ctx.sway(ctx.at(i, offset + index * step), 0.004)
                arp_inst.notes.append(
                    pretty_midi.Note(
                        velocity=ctx.jitter(
                            scale_velocity(spec["velocity"], ctx.vel_scale, accent), 2
                        ),
                        pitch=sequence[index % len(sequence)],
                        start=when,
                        end=when + step * beat * 0.9,
                    )
                )
