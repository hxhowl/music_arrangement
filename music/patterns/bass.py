import pretty_midi

from core.styles import get as get_style
from core.theory import chord_root_pitch, fold_into_range, scale_velocity


def build(bass_inst, ctx):
    spec = get_style(ctx.style)["bass"]
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
                    velocity=scale_velocity(spec["velocity"], ctx.vel_scale, accent),
                    pitch=root + semitone,
                    start=start + offset * beat,
                    end=start + (offset + beats) * beat,
                )
            )
