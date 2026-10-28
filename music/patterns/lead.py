import pretty_midi

from core.theory import CHORDS, PROGRESSION, chord_root_pitch, scale_velocity

TARGET = 69                  # A4，旋律的中心音区
LOW, HIGH = 60, 83

# 动机按「和弦音级」而不是固定半音数取音：
#   MOTIF     根 - 三 - 五 - 三
#   MOTIF_VAR 根 - 五 - 八 - 五
# 旧实现用写死的 [0,7,12,7]，在 A 大三和弦上会得到 C5（小三度），与 C# 直接打架。
MOTIF = (0, 1, 2, 1)
MOTIF_VAR = (0, 2, 3, 2)


def _chord_pitch_classes(chord_name: str) -> set:
    root_pc = chord_root_pitch(chord_name, 0) % 12
    return {(root_pc + semi) % 12 for semi in CHORDS[chord_name]}


def _anchor(chord_name: str, target: int = TARGET) -> int:
    """在 LOW~HIGH 内挑离 target 最近的和弦内音，保证起手音永远落在和弦上。"""
    pcs = _chord_pitch_classes(chord_name)
    candidates = [p for p in range(LOW, HIGH + 1) if p % 12 in pcs]
    return min(candidates, key=lambda p: (abs(p - target), p))


def _chord_tones(chord_name: str, start: int, count: int) -> list:
    """从 start 起向上取 count 个和弦内音，供动机按音级索引。"""
    pcs = _chord_pitch_classes(chord_name)
    tones = []
    pitch = start
    while len(tones) < count and pitch <= HIGH + 12:
        if pitch % 12 in pcs:
            tones.append(pitch)
        pitch += 1
    return tones


def build(lead_inst, bpm, start_bar, num_bars, vel_scale=1.0):
    beat = 60.0 / bpm
    bar_len = 4 * beat

    for i in range(num_bars):
        chord_name = PROGRESSION[i % len(PROGRESSION)]
        tones = _chord_tones(chord_name, _anchor(chord_name), 4)

        # 每 4 小节收一小节呼吸：只留两个长音。
        # 这样 4 个和弦都能拿到旋律（旧实现 i%2 跳过，D/E 整段没旋律）。
        if i % 4 == 3:
            plan = [(0, 0.0, 1.8), (2, 2.0, 1.8)]
        else:
            degrees = MOTIF_VAR if (i // 2) % 2 == 1 else MOTIF
            plan = [(degree, float(j), 0.8) for j, degree in enumerate(degrees)]

        t0 = start_bar * bar_len + i * bar_len
        for degree, beat_offset, beats in plan:
            pitch = tones[degree]
            while pitch > HIGH:
                pitch -= 12
            start = t0 + beat_offset * beat
            lead_inst.notes.append(
                pretty_midi.Note(
                    velocity=scale_velocity(85, vel_scale),
                    pitch=pitch,
                    start=start,
                    end=start + beats * beat,
                )
            )
