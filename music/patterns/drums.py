import pretty_midi
from core.theory import GM_DRUM

def build(drum_inst, bpm, start_bar, num_bars):
    beat = 60.0/bpm
    bar_len = 4*beat
    for i in range(num_bars):
        t0 = start_bar*bar_len + i*bar_len
        # kick 1 3
        for b in [0,2]:
            drum_inst.notes.append(pretty_midi.Note(100, GM_DRUM["kick"], t0+b*beat, t0+b*beat+0.1))
        # snare 2 4
        for b in [1,3]:
            drum_inst.notes.append(pretty_midi.Note(80, GM_DRUM["snare"], t0+b*beat, t0+b*beat+0.1))
        # 8th hat
        for h in range(8):
            drum_inst.notes.append(pretty_midi.Note(45, GM_DRUM["hat"], t0+h*beat*0.5, t0+h*beat*0.5+0.05))