import pretty_midi

from core.theory import GM_DRUM, scale_velocity

# 过门：高音桶 -> 中音桶 -> 低音桶 -> 军鼓，铺满第 4 拍
FILL = (("tom_high", 0.0), ("tom_mid", 0.25), ("tom_low", 0.5), ("snare", 0.75))

# seed 打开的 take 里，反拍偶尔补一记轻踩镲（ghost note），让鼓不那么"打点"
GHOST_OFFSETS = (0.5, 1.5, 2.5, 3.5)


def _add(inst, pitch, start, dur, velocity):
    inst.notes.append(
        pretty_midi.Note(velocity=velocity, pitch=pitch, start=start, end=start + dur)
    )


def _pitch(gm_key: str) -> int:
    if gm_key not in GM_DRUM:
        raise KeyError(f"未知鼓件 {gm_key!r}，可用：{', '.join(GM_DRUM)}")
    return GM_DRUM[gm_key]


def build(drum_inst, ctx):
    """按风格的鼓组谱型演奏；密度档由 arrange 决定，具体怎么打由 style 决定。"""
    if not ctx.density:
        return

    spec = ctx.style_spec["drums"]
    if ctx.density not in spec:
        raise KeyError(f"风格 {ctx.style!r} 没有定义鼓密度 {ctx.density!r}")

    events = spec[ctx.density]
    beat = ctx.beat

    for i in range(ctx.bars):
        start = ctx.bar_time(i)

        if ctx.crash and i == 0:
            _add(drum_inst, _pitch("crash"), start, 0.6,
                 scale_velocity(92, ctx.vel_scale))

        # 过门只出现在满编、每 4 小节末尾，最后一拍让给桶鼓
        do_fill = ctx.fill and ctx.density == "full" and (i + 1) % 4 == 0

        for gm_key, offset, beats, velocity in events:
            if do_fill and offset >= 3.0:
                continue
            _add(
                drum_inst,
                _pitch(gm_key),
                ctx.sway(start + offset * beat, 0.004),   # 鼓摆小一点，太飘会显得不专业
                beats * beat,
                ctx.jitter(scale_velocity(velocity, ctx.vel_scale), 3),
            )

        if do_fill:
            for step, (gm_key, offset) in enumerate(FILL):
                _add(
                    drum_inst,
                    _pitch(gm_key),
                    start + (3.0 + offset) * beat,
                    0.12 * beat,
                    scale_velocity(90, ctx.vel_scale, 1.0 - 0.06 * step),
                )
        elif ctx.density == "full" and ctx.chance(0.35):
            # 只有开了 seed 才会出现；seed=0 的产物保持完全确定
            offset = ctx.rng.choice(GHOST_OFFSETS)
            _add(
                drum_inst,
                _pitch("hat"),
                start + offset * beat,
                0.05 * beat,
                scale_velocity(28, ctx.vel_scale),
            )
