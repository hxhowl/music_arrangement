import pretty_midi

# 根音一律由和弦名推导，不写死 MIDI 数字 —— 否则换调/换和弦即 KeyError，
# 且极易把三音当根音（见 code review P0-4）。
from core.theory import PROGRESSION, chord_root_pitch, fold_into_range, scale_velocity

# 贝斯音区窗口（含端点）：A1(33) ~ G#2(44)。跨和弦按八度折进来，避免上下乱跳，
# 也避免与中频和弦撞在同一个八度。
BASS_LOW = 33
BASS_HIGH = 44


def build(bass_inst, bpm, start_bar, num_bars, root_octave=1, vel_scale=1.0):
    beat = 60.0 / bpm
    bar_len = 4 * beat
    for i in range(num_bars):
        name = PROGRESSION[i % len(PROGRESSION)]
        root = fold_into_range(chord_root_pitch(name, root_octave), BASS_LOW, BASS_HIGH)
        t0 = start_bar * bar_len + i * bar_len
        for b in range(4):
            # 正拍重、反拍略轻，避免四个音完全一个力度
            accent = 1.0 if b == 0 else 0.9
            bass_inst.notes.append(
                pretty_midi.Note(
                    velocity=scale_velocity(90, vel_scale, accent),
                    pitch=root,
                    start=t0 + b * beat,
                    end=t0 + (b + 0.7) * beat,
                )
            )
