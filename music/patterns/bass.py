import pretty_midi

from core.theory import chord_root_pitch, fold_into_range, scale_velocity


def build(bass_inst, ctx):
    """贝斯：按风格的节奏型演奏和弦根音。

    每个音的根音取自它**所在拍位**的和弦（半小节换和弦时不会踩错），
    时长切在换和弦处，不会压过下一个和弦。
    """
    spec = ctx.style_spec["bass"]
    beat = ctx.beat

    for i in range(ctx.bars):
        for offset, beats, accent, semitone in spec["rhythm"]:
            name = ctx.chord_at_beat(i, offset)
            root = fold_into_range(
                chord_root_pitch(name, spec["octave"]), spec["low"], spec["high"]
            )

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
