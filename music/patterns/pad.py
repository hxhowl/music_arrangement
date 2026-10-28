import pretty_midi

from core.theory import chord_root_pitch, scale_velocity


def build(pad_inst, ctx):
    spec = ctx.style_spec["pad"]
    bar_len = ctx.bar_len

    for i in range(ctx.bars):
        name = ctx.chord_at(i)
        root = chord_root_pitch(name, spec["octave"])
        start = ctx.bar_time(i)
        end = start + bar_len * spec["hold"]

        for semitone in spec["intervals"]:
            pad_inst.notes.append(
                pretty_midi.Note(
                    velocity=scale_velocity(spec["velocity"], ctx.vel_scale),
                    pitch=root + semitone,
                    start=start,
                    end=end,
                )
            )
