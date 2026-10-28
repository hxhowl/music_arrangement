import pretty_midi

from core.theory import GM_DRUM, scale_velocity

# 鼓密度档位。None 由编排层直接跳过，不走这里。
#   hat  - 只有踩镲，用于 bridge 这类"悬着"的段落
#   half - 半拍感：底鼓 1、军鼓 3、8 分踩镲
#   full - 满编：底鼓 1/3 + 反拍推进、军鼓 2/4、8 分踩镲、四小节一次过门
DENSITIES = ("hat", "half", "full")

HAT_PATTERN = {
    "hat":  (0.0, 1.0, 2.0, 3.0),
    "half": tuple(k * 0.5 for k in range(8)),
    "full": tuple(k * 0.5 for k in range(8)),
}

# 过门顺序：高音桶 -> 中音桶 -> 低音桶 -> 军鼓
FILL = ("tom_high", "tom_mid", "tom_low", "snare")


def _add(inst, pitch, start, dur, velocity):
    inst.notes.append(
        pretty_midi.Note(velocity=velocity, pitch=pitch, start=start, end=start + dur)
    )


def build(drum_inst, bpm, start_bar, num_bars, density="full", vel_scale=1.0,
          crash=False, fill=True):
    """crash: 段落起点是否加吊镲；fill: 是否每 4 小节加一次过门。"""
    if density not in DENSITIES:
        raise ValueError(f"未知鼓密度 {density!r}，可选: {DENSITIES}")

    beat = 60.0 / bpm
    bar_len = 4 * beat
    hat = GM_DRUM["hat"]
    kick = GM_DRUM["kick"]
    snare = GM_DRUM["snare"]

    for i in range(num_bars):
        t0 = start_bar * bar_len + i * bar_len
        # 过门只在满编、且每 4 小节末尾，最后一小节留给下一段
        do_fill = fill and density == "full" and (i + 1) % 4 == 0

        if crash and i == 0:
            _add(drum_inst, GM_DRUM["crash"], t0, 0.6, scale_velocity(95, vel_scale))

        # 踩镲：正拍重、反拍轻，避免 8 个音一个力度
        for h in HAT_PATTERN[density]:
            on_beat = abs(h - round(h)) < 1e-9
            _add(drum_inst, hat, t0 + h * beat, 0.05,
                 scale_velocity(46, vel_scale, 1.0 if on_beat else 0.75))

        if density == "half":
            _add(drum_inst, kick, t0, 0.10, scale_velocity(105, vel_scale))
            if not do_fill:
                _add(drum_inst, snare, t0 + 2 * beat, 0.10, scale_velocity(85, vel_scale))

        elif density == "full":
            _add(drum_inst, kick, t0, 0.10, scale_velocity(108, vel_scale))
            _add(drum_inst, kick, t0 + 2 * beat, 0.10, scale_velocity(98, vel_scale))
            _add(drum_inst, kick, t0 + 2.75 * beat, 0.08, scale_velocity(70, vel_scale))
            _add(drum_inst, snare, t0 + 1 * beat, 0.10, scale_velocity(92, vel_scale))
            if do_fill:
                for k, key in enumerate(FILL):
                    _add(drum_inst, GM_DRUM[key], t0 + (3 + k * 0.25) * beat, 0.12,
                         scale_velocity(88, vel_scale, 1.0 - 0.05 * k))
            else:
                _add(drum_inst, snare, t0 + 3 * beat, 0.10, scale_velocity(94, vel_scale))

        # 段落最后一小节开镲，收口
        if density == "full" and i == num_bars - 1 and not do_fill:
            _add(drum_inst, GM_DRUM["openhat"], t0 + 3.5 * beat, 0.25,
                 scale_velocity(58, vel_scale))
