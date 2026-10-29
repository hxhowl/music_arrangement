import pretty_midi

from core.theory import chord_root_pitch, scale_velocity, voice_lead


def _pcs(ctx, name):
    root_pc = chord_root_pitch(name, 0) % 12
    return [(root_pc + semi) % 12 for semi in ctx.chords[name]]


def build(chord_inst, ctx):
    """和弦声部：按 voice leading 排列，并跟随和声节奏。

    两件事：
      1) 每个声部找离上一个和弦最近的八度，不再原位硬跳（旧版听起来"块状"）
      2) 按 `ctx.chord_spans()` 分块 —— 半小节换和弦时，同一小节会有两组音
    """
    spec = ctx.style_spec["chords"]
    low, high = spec["range"]
    hold = float(spec["hold"])
    beat = ctx.beat
    previous = None

    for i in range(ctx.bars):
        for offset, span_beats, name in ctx.chord_spans(i):
            voicing = voice_lead(_pcs(ctx, name), previous, low, high)
            previous = voicing or previous

            start = ctx.sway(ctx.at(i, offset))
            end = start + span_beats * beat * hold

            for pitch in voicing:
                chord_inst.notes.append(
                    pretty_midi.Note(
                        velocity=ctx.jitter(
                            scale_velocity(spec["velocity"], ctx.vel_scale)
                        ),
                        pitch=pitch,
                        start=start,
                        end=end,
                    )
                )
