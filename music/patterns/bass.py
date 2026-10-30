import pretty_midi

from core.theory import chord_root_pitch, fold_into_range, scale_velocity

# 与底鼓咬合时补的短音最长几拍（再长会盖掉风格本身的律动）
LOCK_MAX_BEATS = 0.5
# 补音的力度相对风格基准的比例（比正拍轻一点，别抢主音）
LOCK_ACCENT = 0.8


def _root_at(ctx, spec, name):
    return fold_into_range(
        chord_root_pitch(name, spec["octave"]), spec["low"], spec["high"]
    )


def _fill_to_kick(bass_inst, ctx, spec, bar, played):
    """把底鼓落点上"空缺"的位置补成根音。

    不替换风格自己的节奏型，只在 kick 响而 bass 没响的地方补 ——
    这就是"咬合"：低频两块一起发力，听感立刻结实。
    """
    beat = ctx.beat
    for offset in ctx.kicks_in(bar):
        if any(abs(offset - p) < 1e-3 for p in played):
            continue

        name = ctx.chord_at_beat(bar, offset)
        root = _root_at(ctx, spec, name)

        # 时值：到下一个 bass 事件 / 换和弦处，取更近的那个，且不超过 LOCK_MAX_BEATS
        nexts = [p for p in played if p > offset + 1e-9]
        span = min(offset + LOCK_MAX_BEATS, ctx.chord_end_beat(bar, offset))
        if nexts:
            span = min(span, min(nexts))
        if span - offset <= 1e-6:
            continue

        start = ctx.sway(ctx.at(bar, offset))
        bass_inst.notes.append(
            pretty_midi.Note(
                velocity=ctx.jitter(
                    scale_velocity(spec["velocity"], ctx.vel_scale, LOCK_ACCENT)
                ),
                pitch=root,
                start=start,
                end=start + (span - offset) * beat,
            )
        )


def build(bass_inst, ctx):
    """贝斯：按风格的节奏型演奏和弦根音，并跟底鼓咬合。

    每个音的根音取自它**所在拍位**的和弦（半小节换和弦时不会踩错），
    时长切在换和弦处，不会压过下一个和弦。

    咬合（`bass.lock_kick`）：鼓先写，把底鼓拍位登记进 ctx；
    这里只在"kick 响、bass 没响"的位置补一个根音，不改风格自己的节奏型。
    cinematic 那种长音铺底不该被切成一段段，所以它是关的。
    """
    spec = ctx.style_spec["bass"]
    beat = ctx.beat
    lock = bool(spec.get("lock_kick", False))

    for i in range(ctx.bars):
        played = []
        for offset, beats, accent, semitone in spec["rhythm"]:
            name = ctx.chord_at_beat(i, offset)
            root = _root_at(ctx, spec, name)

            # 不让音尾压过换和弦的位置
            end_beat = min(offset + beats, ctx.chord_end_beat(i, offset))
            start = ctx.sway(ctx.at(i, offset))

            bass_inst.notes.append(
                pretty_midi.Note(
                    velocity=ctx.jitter(
                        scale_velocity(spec["velocity"], ctx.vel_scale, accent)
                    ),
                    pitch=root + semitone,
                    start=start,
                    end=start + (end_beat - offset) * beat,
                )
            )
            played.append(offset)

        if lock:
            _fill_to_kick(bass_inst, ctx, spec, i, played)

    # 补进来的音是后追加的，时间上可能比节奏型的音更早 —— 统一按时间排一遍，
    # 免得下游（或人看列表时）以为顺序乱了
    bass_inst.notes.sort(key=lambda n: (n.start, n.pitch))
