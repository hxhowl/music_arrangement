import pretty_midi

from core.theory import chord_root_pitch, scale_velocity

# 句法：每 2 小节一句，四句一循环 —— A、A'（尾巴上扬）、B（另一半素材）、
# A''（收束到根音）。只写 "A A B A" 会听起来像 loop，加变奏才像人写的。
# 第二项是"用第几句素材"：只有一句的风格，B 会退化成 A 的另一种变奏。
MOTIF_CYCLE = (
    (0, "plain"),
    (0, "tail_up"),
    (1, "plain"),
    (0, "cadence"),
)
# 收尾长音最多撑到小节末，别溢出到下一句
CADENCE_STRETCH = 1.6
# 离风格中心音太远时把取音基准拉回中心 —— 否则长段落里旋律会一路往上漂
REGISTER_PULL = 9


def _pitch_classes(chord_name: str, semitones) -> set:
    root_pc = chord_root_pitch(chord_name, 0) % 12
    return {(root_pc + semi) % 12 for semi in semitones}


def _anchor(chord_name: str, semitones, target: int, low: int, high: int) -> int:
    """在 low~high 内挑离 target 最近的和弦内音，保证起手音永远落在和弦上。"""
    pcs = _pitch_classes(chord_name, semitones)
    candidates = [p for p in range(low, high + 1) if p % 12 in pcs]
    if not candidates:
        raise ValueError(f"旋律音区 {low}~{high} 太窄，放不下 {chord_name} 的和弦音")
    return min(candidates, key=lambda p: (abs(p - target), p))


def _chord_tones(chord_name: str, semitones, low: int, high: int) -> list:
    """音区内的全部和弦音（低→高）。按偏移量取音，选出来的一定在音区里。"""
    pcs = _pitch_classes(chord_name, semitones)
    return [p for p in range(low, high + 1) if p % 12 in pcs]


def _root_near(chord_name: str, target: int, low: int, high: int):
    """离 target 最近的和弦根音（用于收束句）。"""
    root_pc = chord_root_pitch(chord_name, 0) % 12
    candidates = [p for p in range(low, high + 1) if p % 12 == root_pc]
    if not candidates:
        return None
    return min(candidates, key=lambda p: (abs(p - target), p))


def _variant(phrase, kind, beats_per_bar):
    """给一个动机做变奏。只改**最后一个音**，其余保持 —— 听得出是同一句，但不再重复。

    kind: plain（原样）/ tail_up（尾巴往上一个和弦音）/ tail_down（往下）/
          cadence（收束：落到根音并把尾音拉长）
    收束用 degree=-1 表示"取根音"，由 build 里单独处理。
    """
    if kind == "plain" or not phrase:
        return phrase

    head, (degree, offset, beats) = phrase[:-1], phrase[-1]

    if kind == "tail_up":
        degree = degree + 1
    elif kind == "tail_down":
        degree = max(0, degree - 1)
    elif kind == "cadence":
        # 收束只拉伸时值，不改音高 —— 强制落到根音时，如果起手音本来就是根音，
        # 整句会变成同一个音（"躺平"），比不落根音难听得多
        room = max(beats, beats_per_bar - offset)      # 本句最后一口气能拖多长
        beats = min(beats * CADENCE_STRETCH, room)
    else:
        raise ValueError(f"未知的变奏类型 {kind!r}")

    return head + [(degree, offset, beats)]


def _end_bar(ctx, end_time, start_bar):
    """这个音结束在哪一小节（段内小节号，夹在本段范围内）。"""
    offset = (end_time - 1e-6) - ctx.bar_time(0)
    index = int(offset // ctx.bar_len) if ctx.bar_len else 0
    return max(start_bar, min(ctx.bars - 1, index))


def build(lead_inst, ctx):
    """主旋律：以风格里的 phrases 为动机素材，按 A / A' / B / A'' 展开。

    旧版是 `phrases[(i // 2) % len(phrases)]` —— 素材只有一两句时，
    整段旋律就是同一句无限循环，听起来像 loop。现在四句一循环，
    第 2、4 句只改尾巴（上扬 / 收束成根音长音），既保持动机统一，又不重复。

    其余规则不变：
      - 每个音用它自己所在拍位的和弦取音级（半小节换和弦也跟得上）
      - 起手音取离上一个音最近的和弦音，让旋律自己连贯
      - seed 只决定"从四句里的哪一句进"，不改变句子本身
    """
    spec = ctx.style_spec["lead"]
    phrases = spec["phrases"]
    breath_every = spec["breath_every"]
    breath = spec["breath"]
    target = spec["target"]
    low, high = spec["range"]
    beat = ctx.beat
    beats_per_bar = ctx.beats_per_bar

    # seed 只换"从哪一句开始"，不改变句子本身，所以还是同一套风格的不同演奏
    offset = (ctx.seed % len(MOTIF_CYCLE)) if ctx.seed else 0
    # 上一个音作为下一个音的"就近目标"，让旋律自身也连贯
    last_pitch = None

    for i in range(ctx.bars):
        if breath_every and i % breath_every == breath_every - 1:
            plan = breath
        else:
            unit = (i // 2 + offset) % len(MOTIF_CYCLE)
            phrase_index, kind = MOTIF_CYCLE[unit]
            phrase = phrases[phrase_index % len(phrases)]
            plan = _variant(phrase, kind, beats_per_bar)

        for degree, offset_beats, beats in plan:
            name = ctx.chord_at_beat(i, offset_beats)
            # 取音基准：平时跟着上一个音走（连贯），跑偏了拉回风格的中心音区（不漂）
            reference = last_pitch if last_pitch is not None else target
            if abs(reference - target) > REGISTER_PULL:
                reference = target
            anchor = _anchor(name, ctx.chords[name], reference, low, high)

            if degree < 0:
                # 收束音：落到根音。找不到根音（音区太窄）就退回 anchor
                pitch = _root_near(
                    name, last_pitch if last_pitch is not None else target, low, high
                ) or anchor
            else:
                # 在音区内的和弦音列表里按偏移量取。数到顶就反过来数 ——
                # 直接截断会让相邻两个音变成同一个音高（旋律会"躺平"）。
                tones = _chord_tones(name, ctx.chords[name], low, high)
                base = tones.index(anchor)
                index = base + degree
                if index >= len(tones):
                    index = base - degree
                pitch = tones[max(0, min(len(tones) - 1, index))]

            # 旋律音可以跨过换和弦的位置（长音压过和声变化是正常写法），不切
            start = ctx.sway(ctx.at(i, offset_beats))
            end = start + beats * beat

            lead_inst.notes.append(
                pretty_midi.Note(
                    velocity=ctx.jitter(scale_velocity(spec["velocity"], ctx.vel_scale)),
                    pitch=pitch,
                    start=start,
                    end=max(end, start + 0.05),
                )
            )
            last_pitch = pitch
            # 登记旋律占用的音高，让 pad / arp 之类的声部避开。
            # 长音会跨小节，所以按它实际盖住的小节登记 —— 只记起始小节的话，
            # 下一小节的 pad 不知道这个音还响着，就会撞上（同频叠置）
            for bar in range(i, _end_bar(ctx, end, i) + 1):
                ctx.occupy(bar, [pitch])
            ctx.register_lead(start, end, pitch)
