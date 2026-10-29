import pretty_midi

from core.theory import chord_root_pitch, scale_velocity, voice_lead


def build(chord_inst, ctx):
    """和弦声部：按 voice leading 排列，不再每小节原位硬跳。

    原位三和弦连续排列时内声部会大跳（听起来"块状"）；这里让每个声部
    找离上一小节最近的八度，声部进行会平滑很多。
    """
    spec = ctx.style_spec["chords"]
    bar_len = ctx.bar_len
    low, high = spec["range"]
    previous = None

    for i in range(ctx.bars):
        name = ctx.chord_at(i)
        root_pc = chord_root_pitch(name, 0) % 12
        pcs = [(root_pc + semi) % 12 for semi in ctx.chords[name]]

        voicing = voice_lead(pcs, previous, low, high)
        previous = voicing or previous

        start = ctx.bar_time(i)
        end = start + bar_len * spec["hold"]

        for pitch in voicing:
            chord_inst.notes.append(
                pretty_midi.Note(
                    velocity=ctx.jitter(scale_velocity(spec["velocity"], ctx.vel_scale)),
                    pitch=pitch,
                    start=ctx.sway(start),
                    end=end,
                )
            )
