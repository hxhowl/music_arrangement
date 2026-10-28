import pretty_midi

from core.styles import get as get_style
from core.theory import GM_DRUM, scale_velocity

# 过门：高音桶 -> 中音桶 -> 低音桶 -> 军鼓，铺满第 4 拍
FILL = (("tom_high", 0.0), ("tom_mid", 0.25), ("tom_low", 0.5), ("snare", 0.75))


def build(drum_inst, ctx):
    """按风格的鼓组谱型演奏；密度档由 arrange 决定，具体怎么打由 style 决定。"""
    if not ctx.density:
        return

    spec = get_style(ctx.style)["drums"]
    if ctx.density not in spec:
        raise KeyError(f"风格 {ctx.style!r} 没有定义鼓密度 {ctx.density!r}")

    events = spec[ctx.density]
    beat = ctx.beat

    for i in range(ctx.bars):
        start = ctx.bar_time(i)

        if ctx.crash and i == 0:
            drum_inst.notes.append(
                pretty_midi.Note(
                    velocity=scale_velocity(92, ctx.vel_scale),
                    pitch=GM_DRUM["crash"],
                    start=start,
                    end=start + 0.6,
                )
            )

        # 过门只出现在满编、每 4 小节末尾，最后一拍让给桶鼓
        do_fill = ctx.fill and ctx.density == "full" and (i + 1) % 4 == 0

        for gm_key, offset, beats, velocity in events:
            if do_fill and offset >= 3.0:
                continue
            drum_inst.notes.append(
                pretty_midi.Note(
                    velocity=scale_velocity(velocity, ctx.vel_scale),
                    pitch=GM_DRUM[gm_key],
                    start=start + offset * beat,
                    end=start + (offset + beats) * beat,
                )
            )

        if do_fill:
            for step, (gm_key, offset) in enumerate(FILL):
                drum_inst.notes.append(
                    pretty_midi.Note(
                        velocity=scale_velocity(90, ctx.vel_scale, 1.0 - 0.06 * step),
                        pitch=GM_DRUM[gm_key],
                        start=start + (3.0 + offset) * beat,
                        end=start + (3.0 + offset + 0.12) * beat,
                    )
                )
