NOTE_OFFSET = {"C":0,"C#":1,"D":2,"D#":3,"E":4,"F":5,"F#":6,"G":7,"G#":8,"A":9,"A#":10,"B":11}

# 和弦库（相对根音半音）
CHORDS = {
    "F#m": [0, 3, 7],
    "D":   [0, 4, 7],
    "A":   [0, 4, 7],
    "E":   [0, 4, 7],
}

# 和弦进行（按小节循环）
PROGRESSION = ["F#m", "D", "A", "E"]

# GM 鼓键位
GM_DRUM = {
    "kick": 36,
    "snare": 38,
    "hat": 42,
    "openhat": 46,
    "clap": 40,
    "tom1": 48,
}

def note_name_to_midi(name: str, octave: int) -> int:
    # name 如 F# -> midi
    return 12 * (octave + 1) + NOTE_OFFSET[name]