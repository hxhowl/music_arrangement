import pretty_midi

CHORDS = {
    "F#m": [0, 3, 7],
    "D":   [0, 4, 7],
    "A":   [0, 4, 7],
    "E":   [0, 4, 7],
}

PROGRESSION = ["F#m", "D", "A", "E"]

NOTE_OFFSET = {"C":0,"C#":1,"D":2,"D#":3,"E":4,"F":5,"F#":6,"G":7,"G#":8,"A":9,"A#":10,"B":11}

def _root_note(chord_name, base_octave=3):
    """从和弦名提取根音 MIDI 音高"""
    # 处理 "F#m" -> "F#", "D" -> "D", "Am" -> "A"
    if chord_name.endswith("m"):
        root_name = chord_name[:-1]
    else:
        root_name = chord_name
    return 12 * (base_octave + 1) + NOTE_OFFSET[root_name]

def build(chord_inst, bpm, start_bar, num_bars, base_octave=3):
    beat = 60.0 / bpm
    bar_len = 4 * beat
    for i in range(num_bars):
        chord_name = PROGRESSION[i % len(PROGRESSION)]
        intervals = CHORDS[chord_name]
        root_midi = _root_note(chord_name, base_octave)
        t0 = start_bar * bar_len + i * bar_len
        for semi in intervals:
            p = root_midi + semi
            chord_inst.notes.append(
                pretty_midi.Note(velocity=55, pitch=p, start=t0, end=t0 + bar_len * 0.9)
            )
