import pretty_midi

from core.theory import GM_DRUM, scale_velocity


def _pitch(gm_key: str) -> int:
    if gm_key not in GM_DRUM:
        raise KeyError(f"未知鼓件 {gm_key!r}，可用：{', '.join(GM_DRUM)}")
    return GM_DRUM[gm_key]


def build(perc_inst, ctx):
    """装饰性打击乐：沙锤 / 铃鼓 / 侧击。

    短视频的"律动感"很大一部分来自这一层：不占低频、不抢人声，
    但抽掉就会立刻显得死板。单独一条轨，方便在 Logic 里单独推拉。
    """
    spec = ctx.style_spec["perc"]
    step = float(spec["step"])
    accents = set(int(a) for a in spec["accents"])
    pitch = _pitch(spec["gm"])
    beat = ctx.beat

    steps = int(round(4 / step))
    for i in range(ctx.bars):
        start = ctx.bar_time(i)
        for index in range(steps):
            accent = 1.0 if index in accents else 0.72
            when = ctx.sway(start + index * step * beat, 0.005)
            perc_inst.notes.append(
                pretty_midi.Note(
                    velocity=ctx.jitter(
                        scale_velocity(spec["velocity"], ctx.vel_scale, accent), 2
                    ),
                    pitch=pitch,
                    start=when,
                    end=when + 0.05,
                )
            )
