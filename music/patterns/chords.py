import pretty_midi

# 和弦数据统一来自 core.theory —— 不要在 pattern 层重复定义。
# 否则改 theory.py 时和弦不跟随，贝斯/旋律会与和弦错位（见 code review P0-1）。
from core.theory import CHORDS, PROGRESSION, note_name_to_midi


def _root_pitch(chord_name: str, octave: int) -> int:
    """从和弦名取根音 MIDI 音高，如 "F#m" -> F#{octave}, "D" -> D{octave}。"""
    name = chord_name[:-1] if chord_name.endswith("m") else chord_name
    return note_name_to_midi(name, octave)


def build(chord_inst, bpm, start_bar, num_bars, base_octave=3):
    beat = 60.0 / bpm
    bar_len = 4 * beat
    for i in range(num_bars):
        chord_name = PROGRESSION[i % len(PROGRESSION)]
        intervals = CHORDS[chord_name]
        root_midi = _root_pitch(chord_name, base_octave)
        t0 = start_bar * bar_len + i * bar_len
        for semi in intervals:
            p = root_midi + semi
            chord_inst.notes.append(
                pretty_midi.Note(velocity=55, pitch=p, start=t0, end=t0 + bar_len * 0.9)
            )
