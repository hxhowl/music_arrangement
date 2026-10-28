import pretty_midi

from core.theory import chord_root_pitch, scale_velocity


def build(chord_inst, ctx):
    spec = ctx.style_spec["chords"]
    bar_len = ctx.bar_len

    for i in range(ctx.bars):
        name = ctx.chord_at(i)
        root = chord_root_pitch(name, spec["octave"])
        start = ctx.bar_time(i)
        end = start + bar_len * spec["hold"]

        for semitone in ctx.chords[name]:
            chord_inst.notes.append(
                pretty_midi.Note(
                    velocity=ctx.jitter(scale_velocity(spec["velocity"], ctx.vel_scale)),
                    pitch=root + semitone,
                    start=start,
                    end=end,
                )
            )
