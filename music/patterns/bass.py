import pretty_midi

from core.theory import chord_root_pitch, fold_into_range, scale_velocity


def build(bass_inst, ctx):
    spec = ctx.style_spec["bass"]
    beat = ctx.beat

    for i in range(ctx.bars):
        name = ctx.chord_at(i)
        root = fold_into_range(
            chord_root_pitch(name, spec["octave"]), spec["low"], spec["high"]
        )
        start = ctx.bar_time(i)

        for offset, beats, accent, semitone in spec["rhythm"]:
            bass_inst.notes.append(
                pretty_midi.Note(
                    velocity=ctx.jitter(scale_velocity(spec["velocity"], ctx.vel_scale, accent)),
                    pitch=root + semitone,
                    start=ctx.sway(start + offset * beat),
                    end=start + (offset + beats) * beat,
                )
            )
