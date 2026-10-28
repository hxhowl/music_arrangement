import pretty_midi
from core.theory import PROGRESSION

def build(bass_inst, bpm, start_bar, num_bars, root_octave=1):
    beat = 60.0/bpm
    bar_len = 4*beat
    base_roots = {"F#m":57,"D":50,"A":45,"E":52}
    for i in range(num_bars):
        name = PROGRESSION[i % len(PROGRESSION)]
        root = base_roots[name]
        t0 = start_bar*bar_len + i*bar_len
        for b in range(4):
            bass_inst.notes.append(
                pretty_midi.Note(velocity=90, pitch=root, start=t0+b*beat, end=t0+(b+0.7)*beat)
            )