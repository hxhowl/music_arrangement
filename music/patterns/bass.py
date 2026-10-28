import pretty_midi

# 根音一律由和弦名推导，不写死 MIDI 数字 —— 否则换调/换和弦即 KeyError，
# 且极易把三音当根音（见 code review P0-4）。
from core.theory import PROGRESSION, note_name_to_midi

# 贝斯音区窗口（含端点）：A1(33) ~ G#2(44)
BASS_LOW = 33
BASS_HIGH = 44


def _bass_root(chord_name: str, octave: int) -> int:
    """把和弦根音折到统一贝斯音区，避免八度乱跳、也避免与中频和弦撞音。"""
    name = chord_name[:-1] if chord_name.endswith("m") else chord_name
    pitch = note_name_to_midi(name, octave)
    while pitch > BASS_HIGH:
        pitch -= 12
    while pitch < BASS_LOW:
        pitch += 12
    return pitch


def build(bass_inst, bpm, start_bar, num_bars, root_octave=1):
    beat = 60.0 / bpm
    bar_len = 4 * beat
    for i in range(num_bars):
        name = PROGRESSION[i % len(PROGRESSION)]
        root = _bass_root(name, root_octave)
        t0 = start_bar * bar_len + i * bar_len
        for b in range(4):
            bass_inst.notes.append(
                pretty_midi.Note(velocity=90, pitch=root, start=t0 + b * beat, end=t0 + (b + 0.7) * beat)
            )
