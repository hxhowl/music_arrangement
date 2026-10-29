import pretty_midi

from core.theory import GM_DRUM, scale_velocity


def _add(inst, pitch, start, dur, velocity):
    inst.notes.append(
        pretty_midi.Note(velocity=velocity, pitch=pitch, start=start, end=start + dur)
    )


def _pitch(gm_key: str) -> int:
    if gm_key not in GM_DRUM:
        raise KeyError(f"未知鼓件 {gm_key!r}，可用：{', '.join(GM_DRUM)}")
    return GM_DRUM[gm_key]


def build(drum_inst, ctx):
    """按风格的鼓组谱型演奏。

    密度档由 arrange 决定；怎么打、过门多密、要不要加装饰音由 style 决定，
    都能在 config.json 的 arrange / style_tweaks 里按这首歌覆盖。
    所有拍位都走 `ctx.at()`，所以开 swing 时鼓也会跟着摇。
    """
    if not ctx.density:
        return

    spec = ctx.style_spec
    levels = spec["drums"]
    if ctx.density not in levels:
        raise KeyError(f"风格 {ctx.style!r} 没有定义鼓密度 {ctx.density!r}")

    events = levels[ctx.density]
    fill = spec["fill"]
    fill_every = int(spec["fill_every"])
    ghost = spec["ghost"]
    ghost_chance = float(ghost.get("chance", 0))
    ghost_velocity = int(ghost.get("velocity", 28))
    beat = ctx.beat
    last_beat = ctx.beats_per_bar - 1  # 过门落在最后一拍

    for i in range(ctx.bars):
        if ctx.crash and i == 0:
            _add(drum_inst, _pitch("crash"), ctx.at(i), 0.6 * beat,
                 scale_velocity(92, ctx.vel_scale))

        # 过门只出现在满编段落，每 fill_every 小节一次，最后一拍让给过门
        do_fill = ctx.fill and ctx.density == "full" and (i + 1) % fill_every == 0

        for gm_key, offset, beats, velocity in events:
            if do_fill and offset >= last_beat:
                continue
            _add(
                drum_inst,
                _pitch(gm_key),
                ctx.sway(ctx.at(i, offset), 0.004),   # 鼓摆小一点，太飘会显得不专业
                beats * beat,
                ctx.jitter(scale_velocity(velocity, ctx.vel_scale), 3),
            )

        if do_fill:
            for step, (gm_key, offset) in enumerate(fill):
                _add(
                    drum_inst,
                    _pitch(gm_key),
                    ctx.at(i, last_beat + offset),
                    0.12 * beat,
                    scale_velocity(90, ctx.vel_scale, 1.0 - 0.06 * step),
                )
        elif ctx.density == "full" and ghost_chance and ctx.chance(ghost_chance):
            # 只有开了 seed 才会出现；seed=0 的产物保持完全确定
            offset = ctx.rng.choice((0.5, 1.5, 2.5, 3.5))
            _add(
                drum_inst,
                _pitch("hat"),
                ctx.at(i, offset),
                0.05 * beat,
                scale_velocity(ghost_velocity, ctx.vel_scale),
            )
