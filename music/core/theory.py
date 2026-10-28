NOTE_OFFSET = {"C":0,"C#":1,"D":2,"D#":3,"E":4,"F":5,"F#":6,"G":7,"G#":8,"A":9,"A#":10,"B":11}

# 和弦库（相对根音半音）—— 全项目唯一一份，pattern 层不要再重复定义
CHORDS = {
    "F#m": [0, 3, 7],
    "D":   [0, 4, 7],
    "A":   [0, 4, 7],
    "E":   [0, 4, 7],
}

# 和弦进行（按小节循环）
PROGRESSION = ["F#m", "D", "A", "E"]

# GM 鼓键位（channel 10，0-index 9）
GM_DRUM = {
    "kick": 36,
    "snare": 38,
    "clap": 40,
    "hat": 42,
    "openhat": 46,
    "tom_low": 45,
    "tom_mid": 47,
    "tom_high": 50,
    "crash": 49,
    "ride": 51,
}


def chord_root_name(chord_name: str) -> str:
    """从和弦名取根音音名：F#m -> F#，Am7 -> A，Dsus4 -> D。

    只解析开头的 [A-G][#b]，后缀（m/7/sus4/add9…）忽略。
    降号写法暂不支持，会给出明确报错，避免静默算错音。
    """
    name = chord_name.strip()
    if not name or name[0] not in "ABCDEFG":
        raise ValueError(f"无法解析和弦名: {chord_name!r}")
    root = name[0]
    if len(name) > 1 and name[1] in "#b":
        root += name[1]
    if root not in NOTE_OFFSET:
        raise ValueError(f"暂不支持的和弦根音 {root!r}（请改用升号写法，如 Db 写成 C#）")
    return root


def note_name_to_midi(name: str, octave: int) -> int:
    """音名+八度 -> MIDI 音高，如 ("F#", 2) -> 42。"""
    return 12 * (octave + 1) + NOTE_OFFSET[name]


def chord_root_pitch(chord_name: str, octave: int) -> int:
    """和弦名 + 八度 -> 根音 MIDI 音高，如 ("F#m", 2) -> 42。"""
    return note_name_to_midi(chord_root_name(chord_name), octave)


def fold_into_range(pitch: int, low: int, high: int) -> int:
    """把音高按八度折进 [low, high]，跨和弦时不乱跳。"""
    while pitch > high:
        pitch -= 12
    while pitch < low:
        pitch += 12
    return pitch


def scale_velocity(base: int, scale: float = 1.0, accent: float = 1.0) -> int:
    """基准力度按段落/主控缩放，夹在 MIDI 合法区间 1..127。"""
    return max(1, min(127, int(round(base * scale * accent))))
