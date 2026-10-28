"""乐理工具：调性、级数、和弦推导、GM 映射。

和弦不再写死。config 里给 key + 级数（如 "Am" + ["i","VI","III","VII"]），
这里推导出实际和弦（Am - F - C - G）。音名按调号正确拼写，D 小调的 VI 级是 Bb 而不是 A#。
"""

LETTERS = ("C", "D", "E", "F", "G", "A", "B")
NATURAL_PCS = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}

# 音名 -> 音级（仅升号写法，供外部查表用；实际解析见 parse_note）
NOTE_OFFSET = {"C":0,"C#":1,"D":2,"D#":3,"E":4,"F":5,"F#":6,"G":7,"G#":8,"A":9,"A#":10,"B":11}

# 调式（相对主音半音）
SCALES = {
    "major": (0, 2, 4, 5, 7, 9, 11),
    "minor": (0, 2, 3, 5, 7, 8, 10),   # 自然小调
}

# 级数 -> 音阶内下标。大小写不敏感：i 和 I 都指第一级，
# 和弦性质由调式推导，不由字母大小写决定。
DEGREES = {"I": 0, "II": 1, "III": 2, "IV": 3, "V": 4, "VI": 5, "VII": 6}

# 默认进行按调式给：小调用 i-VI-III-VII（F#m 下即 F#m-D-A-E），
# 大调用 I-V-vi-IV。用错调式的进行会算出 Bdim 这种怪和弦。
DEFAULT_PROGRESSIONS = {
    "minor": ["i", "VI", "III", "VII"],
    "major": ["I", "V", "vi", "IV"],
}

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


def parse_note(name: str) -> int:
    """音名 -> 音级 0~11。支持 F# / Bb / C## 等写法。"""
    text = (name or "").strip()
    if not text or text[0] not in NATURAL_PCS:
        raise ValueError(f"无法解析音名 {name!r}（示例：C / F# / Bb）")

    accidentals = text[1:]
    if any(ch not in "#b" for ch in accidentals):
        raise ValueError(f"音名 {name!r} 的后缀只能是 # 或 b")

    pitch = NATURAL_PCS[text[0]] + accidentals.count("#") - accidentals.count("b")
    return pitch % 12


def note_name_to_midi(name: str, octave: int) -> int:
    """音名+八度 -> MIDI 音高，如 ("F#", 2) -> 42。"""
    return 12 * (octave + 1) + parse_note(name)


def spell_pitch(pitch: int, letter: str) -> str:
    """把音级写成指定字母的音名：spell_pitch(10, "B") -> "Bb"。"""
    diff = (pitch - NATURAL_PCS[letter]) % 12
    if diff == 0:
        return letter
    if diff == 1:
        return letter + "#"
    if diff == 2:
        return letter + "##"
    if diff == 11:
        return letter + "b"
    if diff == 10:
        return letter + "bb"
    raise ValueError(f"音级 {pitch} 无法写成 {letter} 系的音名")


def parse_key(key: str):
    """把调性拆成 (主音音名, 调式)：'Am' -> ('A','minor')，'Bb' -> ('Bb','major')。"""
    text = (key or "").strip()
    if not text or text[0] not in NATURAL_PCS:
        raise ValueError(f"无法解析调性 {key!r}（写法示例：C / Am / F#m / Bb）")

    root = text[0]
    index = 1
    if len(text) > 1 and text[1] in "#b":
        root += text[1]
        index = 2
    parse_note(root)   # 校验音名合法

    suffix = text[index:].strip().lower()
    if suffix in ("", "maj", "major"):
        mode = "major"
    elif suffix in ("m", "min", "minor"):
        mode = "minor"
    else:
        raise ValueError(f"无法识别调式后缀 {suffix!r}（只支持大调 C 与小调 Am 两种写法）")
    return root, mode


def scale_pitch_classes(key: str):
    """调内七个音的音级（0~11），按级数顺序。"""
    root, mode = parse_key(key)
    tonic = parse_note(root)
    return [(tonic + semi) % 12 for semi in SCALES[mode]]


def degree_to_chord(key: str, degree: str):
    """级数 -> (和弦名, 相对根音的半音列表)。

    ('Am', 'i')  -> ('Am', [0, 3, 7])
    ('Am', 'VI') -> ('F',  [0, 4, 7])
    ('Dm', 'VI') -> ('Bb', [0, 4, 7])
    ('C',  'vi') -> ('Am', [0, 3, 7])
    """
    deg = DEGREES.get(str(degree).strip().upper())
    if deg is None:
        raise ValueError(f"无法解析级数 {degree!r}（可用：{'/'.join(DEGREES)}）")

    root, _ = parse_key(key)
    root_letter = LETTERS.index(root[0])
    pcs = scale_pitch_classes(key)

    root_pc = pcs[deg]
    third = (pcs[(deg + 2) % 7] - root_pc) % 12
    fifth = (pcs[(deg + 4) % 7] - root_pc) % 12

    if (third, fifth) == (3, 7):
        suffix = "m"
    elif (third, fifth) == (4, 7):
        suffix = ""
    elif (third, fifth) == (3, 6):
        suffix = "dim"
    elif (third, fifth) == (4, 8):
        suffix = "aug"
    else:
        raise ValueError(f"调 {key} 的第 {degree} 级算不出常见三和弦（三音{third}/五音{fifth}）")

    # 按调号的字母顺序拼写：D 小调的 VI 级是 Bb，不是 A#
    letter = LETTERS[(root_letter + deg) % 7]
    name = spell_pitch(root_pc, letter) + suffix
    return name, [0, third, fifth]


def build_progression(key: str, degrees):
    """级数列表 -> (和弦名列表, {和弦名: 半音列表})。"""
    if not degrees:
        raise ValueError("progression 不能为空")

    names = []
    chord_map = {}
    for degree in degrees:
        name, semitones = degree_to_chord(key, degree)
        names.append(name)
        chord_map[name] = semitones
    return names, chord_map


def default_progression(key: str):
    """按调式给一条稳当的默认进行：小调 i-VI-III-VII，大调 I-V-vi-IV。"""
    _, mode = parse_key(key)
    return list(DEFAULT_PROGRESSIONS[mode])


def chord_root_name(chord_name: str) -> str:
    """从和弦名取根音音名：F#m -> F#，Bbdim -> Bb，Am7 -> A。"""
    name = chord_name.strip()
    root = name[:1]
    if len(name) > 1 and name[1] in "#b":
        root += name[1]
    parse_note(root)
    return root


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
