import pretty_midi

from core.theory import PROGRESSION, chord_root_pitch, scale_velocity

# 开放五度堆叠：8 度 + 12 度 + 2 个 8 度。
# 不叠三音 —— 三音由 chords 轨负责，pad 再叠一遍只会把中频糊掉。
PAD_INTERVALS = (12, 19, 24)


def build(pad_inst, bpm, start_bar, num_bars, base_octave=3, vel_scale=1.0):
    beat = 60.0 / bpm
    bar_len = 4 * beat
    for i in range(num_bars):
        chord_name = PROGRESSION[i % len(PROGRESSION)]
        root = chord_root_pitch(chord_name, base_octave)
        t0 = start_bar * bar_len + i * bar_len
        for semi in PAD_INTERVALS:
            pad_inst.notes.append(
                pretty_midi.Note(
                    velocity=scale_velocity(40, vel_scale),
                    pitch=root + semi,
                    start=t0,
                    end=t0 + bar_len,   # 铺满整小节，段落之间无缝
                )
            )
