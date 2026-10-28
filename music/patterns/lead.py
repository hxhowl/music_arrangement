import pretty_midi
from core.theory import PROGRESSION, CHORDS

def build(lead_inst, bpm, start_bar, num_bars):
    beat = 60.0/bpm
    bar_len = 4*beat
    motif = [0, 7, 12, 7]  # 半音动机
    for i in range(num_bars):
        if i % 2 == 1:
            continue  # 留白
        t0 = start_bar*bar_len + i*bar_len
        root = 69  # A4 起手
        for j, semi in enumerate(motif):
            start = t0 + j*beat
            lead_inst.notes.append(
                pretty_midi.Note(velocity=85, pitch=root+semi, start=start, end=start+beat*0.8)
            )