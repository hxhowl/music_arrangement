import pretty_midi

from core.theory import chord_root_pitch, scale_velocity

TONE_COUNT = 4
# 上方对位与主旋律的最小间隔（半音）。3 = 小三度；再近就是同度/二度，会打架。
MIN_INTERVAL = 3
# 上方对位最多比主旋律高多少（半音）。10 = 小十度，再高就飘走了。
HIGH_SPAN = 10
# 上方对位的上限（E6）。再高就进"叮叮"区，和琶音、音铃抢位置。
DESCANT_TOP = 88


def _tones(name: str, semitones, low: int, high: int, target: int):
    """在 low~high 内从离 target 最近的和弦音起，向上取 4 个音级。

    取音**严格限制在窗口内**：早先允许越到 high+12 再由调用方按八度折回，
    但不足一个八度的越界折不动，会漏出窗口之外的音（高位声部曾漏到 93）。
    """
    root_pc = chord_root_pitch(name, 0) % 12
    pcs = {(root_pc + semi) % 12 for semi in semitones}
    inside = [p for p in range(low, high + 1) if p % 12 in pcs]
    if not inside:
        return []
    anchor = min(inside, key=lambda p: (abs(p - target), p))

    tones = []
    pitch = anchor
    while len(tones) < TONE_COUNT and pitch <= high:
        if pitch % 12 in pcs:
            tones.append(pitch)
        pitch += 1
    return tones


def _sounding_lead(ctx, start, end):
    """[start, end) 内正在响的主旋律音高。"""
    return [p for s, e, p in ctx.lead_notes
            if s < end - 1e-6 and start < e - 1e-6]


def build(counter_inst, ctx):
    """副旋律：主旋律旁边补一条答句。高低两种声部是两种写法，规则不一样。

    设计原则（这几条决定了它是"副旋律"而不是"第二条主旋律"）：

      1) low  —— "回话"：**只在主旋律空着的时候写**。同一个音区里两条线同时响，
         注意力就散了，那就不叫 counter 了。音区用风格给的窗口。
      2) high —— "上方对位"：**允许和主旋律同时响**，位置跟着主旋律走 ——
         落在它上方 3~10 个半音之间，取最近的和弦音。
         跟 low 的规则相反是有意的：下方同时响会糊，上方同时响才叫分层。
         主旋律本身已经很高（窗口越过 DESCANT_TOP）时它就不出声 ——
         再往上堆只会刺耳，这跟真人编曲的选择一致。
      3) 用和弦音级取音，音高由"离上一个音最近"决定，保持自己的连贯
      4) 无论哪种声部，**同音高同时响一律不写** —— 会把旋律轮廓磨平
    """
    spec = ctx.style_spec["counter"]
    low, high = spec["range"]
    target = spec.get("target", (low + high) // 2)
    high_voice = (ctx.counter_voice or spec.get("voice", "low")) == "high"
    beat = ctx.beat
    last_pitch = None

    for i in range(ctx.bars):
        for offset, beats, degree in spec["rhythm"]:
            start = ctx.at(i, offset)
            end = start + beats * beat

            sounding = _sounding_lead(ctx, start, end)
            if sounding and high_voice:
                # 跟着主旋律上移，只取它上方 3~10 个半音内的和弦音
                win_low = max(sounding) + MIN_INTERVAL
                win_high = min(DESCANT_TOP, win_low + HIGH_SPAN)
                anchor = win_low
                if win_low > win_high:
                    continue      # 主旋律已经太高，再往上只会刺耳
            elif sounding:
                continue          # low 声部：主旋律在响就不写
            else:
                win_low, win_high = low, high
                anchor = last_pitch if last_pitch is not None else target

            name = ctx.chord_at_beat(i, offset)
            tones = _tones(name, ctx.chords[name], win_low, win_high, anchor)
            if not tones:
                continue

            # 高位声部只取窗口里最靠下的两个和弦音（约三度/五度），
            # 再往上是八度加倍，那已经不是"对位"了
            index = min(degree, 1) if (sounding and high_voice) else degree
            pitch = tones[min(index, len(tones) - 1)]

            # 与主旋律同音高同时又响：直接放弃这一颗
            if pitch in sounding:
                continue

            counter_inst.notes.append(
                pretty_midi.Note(
                    velocity=ctx.jitter(
                        scale_velocity(spec["velocity"], ctx.vel_scale)
                    ),
                    pitch=pitch,
                    start=ctx.sway(start),
                    end=end,
                )
            )
            last_pitch = pitch
            # 登记占用，让后面构建的 pad 让开（同音叠置会让副旋律的轮廓变模糊）
            ctx.occupy(i, [pitch])
