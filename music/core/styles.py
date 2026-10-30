"""风格库。

每套风格只描述「怎么演奏」，不决定「哪一段出声」——那是 arrange.py 的事。
所以同一份 ARRANGE（intro 没鼓 / verse 中等 / chorus 满）在不同风格下会得到
完全不同的鼓组，这正是"同一句话换风格 = 另一首歌"的关键。

这里的条目是**出厂默认**。项目要微调就用 config.json 的 style_tweaks 覆盖
（见 resolve），不要直接改这里 —— 改这里会影响所有同风格项目。

数据结构：
  chords : octave / hold(占小节比例) / velocity / range=(最低, 最高) / seventh(是否用七和弦)
           beats=每个和弦占几拍（4=一小节一个，2=半小节一个，8=两小节一个）
  bass   : octave / low / high / velocity / rhythm=[(起始拍, 时长拍, accent, 半音偏移)]
           lock_kick=True 时在底鼓落点上补根音（长音铺底型如 cinematic 应关掉）
  drums  : {密度档: [(GM键名, 起始拍, 时长拍, 基准力度)]}
  lead   : target(中心音区) / range=(最低音, 最高音) / breath_every(每 N 小节呼吸，0=不呼吸)
           breath=[(音级, 起始拍, 时长拍)] 呼吸小节用的长音
           phrases=[[(音级, 起始拍, 时长拍)]]，音级是"和弦内第几个音"（0=根音，往上数）
           这同一份素材会被 lead.py 按 A / A' / B / A'' 展开：第 2 句尾音往上挪一级、
           第 4 句把尾音拉长。想换旋律是换 phrases，不是指望"多加一句就不重复"
  pad    : octave / intervals / velocity / hold / duck(有旋律时压低的比例)
  fill   : [(GM键名, 起始拍偏移)] 过门音符，铺满第 4 拍
  fill_every : 每 N 小节加一次过门
  ghost  : dict(chance=概率, velocity=力度) 反拍补的轻踩镲；chance=0 表示不加
  humanize : dict(velocity=力度扰动幅度, sway=时值摆动秒数)，只在 seed>0 时生效
  perc   : dict(gm=鼓件, step=间隔拍, velocity=力度, accents=重拍位置)
  arp    : dict(range=(最低, 最高), step=间隔拍, velocity=力度, octaves=跨几个八度)
  counter: dict(range=(最低, 最高), velocity=力度, target=中心音,
                voice="low"|"high", rhythm=[(起始拍, 时长拍, 音级)])
           副旋律，只在主旋律空着的地方出声。voice 决定它在主旋律的**哪一侧**：
           low = 压在下面当"回话"（大提琴/巴松这种低音区乐器）；
           high = 抬到上面当"上方对位"（中提琴/圆号这种，副歌加层次用）
"""

import copy

from core.theory import GM_DRUM

# 通用过门：高音桶 -> 中音桶 -> 低音桶 -> 军鼓，铺满第 4 拍
FILL_STD = (("tom_high", 0.0), ("tom_mid", 0.25), ("tom_low", 0.5), ("snare", 0.75))
# 通用呼吸小节：两个长音
BREATH_STD = ((0, 0.0, 1.8), (2, 2.0, 1.8))

# 副旋律相对主旋律的位置：低（回话）/ 高（上方对位）
COUNTER_VOICES = ("low", "high")


def _eighths(gm_key: str, base: int, length: float = 0.05):
    """8 分音符，正拍重、反拍轻。"""
    return [(gm_key, i * 0.5, length, base if i % 2 == 0 else int(base * 0.72)) for i in range(8)]


def _quarters(gm_key: str, base: int, length: float = 0.06):
    return [(gm_key, float(i), length, base if i % 2 == 0 else int(base * 0.8)) for i in range(4)]


STYLES = {
    # 电影感：长音铺底、鼓只做心跳、旋律大跳
    "cinematic": dict(
        chords=dict(octave=3, hold=0.99, velocity=46, range=(48, 67), beats=8),
        bass=dict(octave=1, low=33, high=44, velocity=74,
                  rhythm=[(0.0, 3.9, 1.0, 0)], lock_kick=False),
        drums={
            "light":  [("kick", 0.0, 0.25, 52)],
            "medium": [("kick", 0.0, 0.25, 72), ("kick", 1.75, 0.2, 44)],
            "full":   [("kick", 0.0, 0.25, 96), ("kick", 2.0, 0.25, 84),
                       ("snare", 2.0, 0.22, 66), ("tom_low", 3.75, 0.3, 58)],
        },
        lead=dict(target=69, range=(60, 83), velocity=84, breath_every=0, breath=BREATH_STD,
                  phrases=[[(0, 0.0, 1.9), (2, 2.0, 1.9)],
                           [(0, 0.0, 1.9), (3, 2.0, 1.9)]]),   # 第二句尾巴跳一个八度
        pad=dict(octave=3, intervals=(12, 19, 24), velocity=42, hold=1.0, duck=0.72),
        fill=FILL_STD, fill_every=4,
        ghost=dict(chance=0.0, velocity=28),
        perc=dict(gm="shaker", step=1.0, velocity=32, accents=(0,)),
        arp=dict(range=(60, 79), step=0.5, velocity=38, octaves=2),
        counter=dict(range=(52, 69), velocity=54, voice="low",
                     rhythm=[(0.0, 1.8, 2), (2.5, 1.2, 1)]),   # 长音答句
        humanize=dict(velocity=3, sway=0.008),   # 心跳鼓不加装饰音
    ),

    # 流行：标准 4/4，贝斯八分推进到五度
    "pop": dict(
        chords=dict(octave=3, hold=0.88, velocity=58, range=(48, 67), beats=4),
        bass=dict(octave=1, low=33, high=44, velocity=88,
                  rhythm=[(0.0, 0.45, 1.0, 0), (1.0, 0.45, 0.85, 0),
                          (2.0, 0.45, 1.0, 0), (2.5, 0.4, 0.75, 7),
                          (3.0, 0.45, 0.85, 0)], lock_kick=True),
        drums={
            "light":  [("kick", 0.0, 0.1, 72)] + _eighths("hat", 34),
            "medium": [("kick", 0.0, 0.1, 88), ("snare", 2.0, 0.1, 74)] + _eighths("hat", 40),
            "full":   [("kick", 0.0, 0.1, 105), ("kick", 1.5, 0.1, 78),
                       ("kick", 2.0, 0.1, 95), ("kick", 2.75, 0.08, 62),
                       ("snare", 1.0, 0.1, 90), ("snare", 3.0, 0.1, 92)] + _eighths("hat", 46),
        },
        lead=dict(target=69, range=(60, 83), velocity=84, breath_every=4, breath=BREATH_STD,
                  phrases=[
                      [(0, 0.0, 0.8), (1, 1.0, 0.8), (2, 2.0, 0.8), (1, 3.0, 0.8)],
                      [(0, 0.0, 0.8), (2, 1.0, 0.8), (3, 2.0, 0.8), (2, 3.0, 0.8)],
                  ]),
        pad=dict(octave=3, intervals=(12, 16, 19), velocity=34, hold=0.98, duck=0.75),
        fill=FILL_STD, fill_every=4,
        ghost=dict(chance=0.35, velocity=28),
        perc=dict(gm="tambourine", step=0.5, velocity=40, accents=(1, 3)),
        arp=dict(range=(60, 79), step=0.25, velocity=42, octaves=2),
        counter=dict(range=(55, 71), velocity=62, voice="low",
                     rhythm=[(1.5, 0.45, 3), (3.5, 0.45, 2)]),   # 反拍答句
        humanize=dict(velocity=3, sway=0.008),
    ),

    # 慵懒：切分贝斯、半拍鼓、短句重复
    "lofi": dict(
        chords=dict(octave=3, hold=0.72, velocity=52, range=(48, 67), seventh=True, beats=2),
        bass=dict(octave=1, low=33, high=44, velocity=80,
                  rhythm=[(0.0, 0.7, 1.0, 0), (0.75, 0.4, 0.6, 0),
                          (1.5, 0.5, 0.85, 0), (2.5, 0.6, 0.9, 7)], lock_kick=True),
        drums={
            "light":  [("kick", 0.0, 0.1, 54)] + _quarters("hat", 26),
            "medium": [("kick", 0.0, 0.12, 78), ("snare", 2.0, 0.12, 58)]
                      + _eighths("hat", 30),
            "full":   [("kick", 0.0, 0.12, 88), ("kick", 1.75, 0.1, 60),
                       ("snare", 2.0, 0.12, 70)] + _eighths("hat", 36),
        },
        lead=dict(target=69, range=(60, 83), velocity=84, breath_every=4, breath=BREATH_STD,
                  phrases=[
                      [(0, 0.0, 0.55), (1, 0.75, 0.45), (1, 1.5, 0.45), (2, 2.5, 0.9)],
                      [(0, 0.0, 0.55), (2, 0.5, 0.45), (1, 1.25, 0.45), (3, 2.5, 0.9)],
                  ]),
        pad=dict(octave=3, intervals=(12, 19), velocity=32, hold=0.92, duck=0.75),
        fill=FILL_STD, fill_every=4,
        ghost=dict(chance=0.35, velocity=24),
        perc=dict(gm="shaker", step=0.5, velocity=30, accents=(0, 2)),
        arp=dict(range=(57, 76), step=0.5, velocity=36, octaves=2),
        counter=dict(range=(55, 71), velocity=56, voice="low",
                     rhythm=[(1.0, 0.5, 1), (3.0, 0.6, 2)]),   # 切分答句
        humanize=dict(velocity=3, sway=0.008),
    ),

    # 无厘头：断奏和弦、错位重音、大跳旋律
    "playful": dict(
        chords=dict(octave=3, hold=0.35, velocity=66, range=(50, 69), beats=4),
        # 贝斯音区比其它风格低一个窗口：这套律动有 +12 的八度跳，
        # 窗口太高会把贝斯顶到 G3，和 chords 轨撞在一起
        bass=dict(octave=1, low=26, high=38, velocity=92,
                  rhythm=[(0.0, 0.35, 1.0, 0), (0.5, 0.35, 0.55, 12),
                          (2.0, 0.35, 1.0, 0), (2.75, 0.5, 0.7, 7)], lock_kick=True),
        drums={
            "light":  [("kick", 0.0, 0.1, 70), ("hat", 2.0, 0.05, 48)],
            "medium": [("kick", 0.0, 0.1, 92), ("snare", 2.5, 0.1, 70)]
                      + _eighths("hat", 42),
            "full":   [("kick", 0.0, 0.1, 108), ("kick", 1.5, 0.1, 86),
                       ("snare", 1.0, 0.1, 95), ("snare", 3.0, 0.1, 98),
                       ("tom_high", 3.5, 0.1, 78)] + _eighths("hat", 48),
        },
        lead=dict(target=72, range=(60, 83), velocity=84, breath_every=4, breath=BREATH_STD,
                  phrases=[
                      [(0, 0.0, 0.4), (2, 0.5, 0.4), (1, 1.0, 0.4),
                       (3, 2.0, 0.4), (2, 2.5, 0.4)],
                      [(3, 0.0, 0.4), (1, 0.5, 0.4), (0, 1.0, 0.6), (2, 2.5, 0.8)],
                  ]),
        pad=dict(octave=3, intervals=(12, 19, 24), velocity=28, hold=0.9, duck=0.7),
        fill=FILL_STD, fill_every=4,
        ghost=dict(chance=0.45, velocity=30),
        perc=dict(gm="rim", step=0.5, velocity=36, accents=(1,)),
        arp=dict(range=(64, 84), step=0.25, velocity=48, octaves=2),
        counter=dict(range=(57, 74), velocity=66, voice="low",
                     rhythm=[(0.75, 0.35, 3), (2.75, 0.35, 2)]),   # 错位答句
        humanize=dict(velocity=3, sway=0.008),
    ),
}


def get(name: str) -> dict:
    if name not in STYLES:
        raise KeyError(f"未知风格 {name!r}：可选 {', '.join(STYLES)}")
    return STYLES[name]


def resolve(name: str, tweaks: dict = None) -> dict:
    """取一份风格，并叠加项目内的微调。

    tweaks 形如 {"bass": {"velocity": 70}, "drums": {"full": [...]}}，
    只覆盖给出的键。返回的是副本，**不会改动全局 STYLES** ——
    所以同一风格的不同项目可以各自微调，互不影响。
    """
    spec = copy.deepcopy(get(name))
    if not tweaks:
        return spec

    if not isinstance(tweaks, dict):
        raise ValueError("config.style_tweaks 必须是对象")

    unknown = set(tweaks) - set(spec)
    if unknown:
        raise ValueError(
            f"config.style_tweaks 里有未知分组 {sorted(unknown)}，可用：{', '.join(spec)}"
        )

    for group, patch in tweaks.items():
        base = spec[group]
        if isinstance(base, dict):
            if not isinstance(patch, dict):
                raise ValueError(f"config.style_tweaks[{group!r}] 必须是对象")
            unknown = set(patch) - set(base)
            if unknown:
                raise ValueError(
                    f"config.style_tweaks[{group!r}] 里有未知字段 {sorted(unknown)}，"
                    f"可用：{', '.join(base)}"
                )
            base.update(patch)
        else:
            # 标量/列表类字段（fill、fill_every、ghost 之类）整块替换
            spec[group] = patch

    _check_shapes(spec)
    return spec


def _check_shapes(spec: dict) -> None:
    """检查常见手写错误：元组长度、音区宽度、鼓件名、旋律音级。

    这些错如果不提前拦，会在生成到一半时报 KeyError / ValueError，
    信息还不指向 config。
    """
    bass = spec["bass"]
    if bass["high"] - bass["low"] < 11:
        raise ValueError(
            f"bass 音区 low={bass['low']} high={bass['high']} 太窄"
            f"（至少跨 12 个半音，否则八度折叠会算出腔外的音）"
        )
    for item in bass["rhythm"]:
        if len(item) != 4:
            raise ValueError(f"bass.rhythm 每项应为 (起始拍, 时长拍, accent, 半音偏移)，收到 {item!r}")
    if not isinstance(bass.get("lock_kick", False), bool):
        raise ValueError(f"bass.lock_kick={bass.get('lock_kick')!r} 必须是 true/false")

    for level, events in spec["drums"].items():
        for item in events:
            if len(item) != 4:
                raise ValueError(
                    f"drums[{level!r}] 每项应为 (GM 键名, 起始拍, 时长拍, 基准力度)，收到 {item!r}"
                )
            if item[0] not in GM_DRUM:
                raise ValueError(
                    f"drums[{level!r}] 里有未知鼓件 {item[0]!r}，可用：{', '.join(GM_DRUM)}"
                )

    lead = spec["lead"]
    low, high = lead["range"]
    if not low < high:
        raise ValueError(f"lead.range={lead['range']!r} 不合法，应为 (最低音, 最高音)")
    if not 1 <= int(lead["velocity"]) <= 127:
        raise ValueError(f"lead.velocity={lead['velocity']!r} 应在 1~127")
    if len(lead["breath"]) and len(lead["breath"][0]) != 3:
        raise ValueError(f"lead.breath 每项应为 (音级, 起始拍, 时长拍)，收到 {lead['breath']!r}")
    for phrase in lead["phrases"] + [lead["breath"]]:
        for item in phrase:
            if len(item) != 3:
                raise ValueError(
                    f"lead 的乐句每项应为 (音级, 起始拍, 时长拍)，收到 {item!r}"
                )
            if not 0 <= int(item[0]) <= 3:
                raise ValueError(
                    f"lead 乐句的音级 {item[0]!r} 越界，只能是 0~3（和弦内第 1~4 个音）"
                )

    if not isinstance(spec["fill_every"], int) or spec["fill_every"] < 1:
        raise ValueError(f"fill_every={spec['fill_every']!r} 必须是 >=1 的整数")
    for item in spec["fill"]:
        if len(item) != 2:
            raise ValueError(f"fill 每项应为 (GM 键名, 起始拍偏移)，收到 {item!r}")
        if item[0] not in GM_DRUM:
            raise ValueError(f"fill 里有未知鼓件 {item[0]!r}，可用：{', '.join(GM_DRUM)}")

    ghost = spec["ghost"]
    if not isinstance(ghost, dict) or set(ghost) - {"chance", "velocity"}:
        raise ValueError(f"ghost 应为 {{'chance': 0~1, 'velocity': 1~127}}，收到 {ghost!r}")
    if not 0 <= float(ghost.get("chance", 0)) <= 1:
        raise ValueError(f"ghost.chance={ghost.get('chance')!r} 应在 0~1")

    chords = spec["chords"]
    low, high = chords["range"]
    if not low < high:
        raise ValueError(f"chords.range={chords['range']!r} 不合法，应为 (最低音, 最高音)")
    if not 0.5 <= float(chords.get("beats", 4)) <= 16:
        raise ValueError(
            f"chords.beats={chords.get('beats')!r} 不合理：应在 0.5~16 拍之间"
            f"（4 = 一小节一个和弦，2 = 半小节一个，8 = 两小节一个）"
        )

    counter = spec["counter"]
    low, high = counter["range"]
    if not low < high:
        raise ValueError(f"counter.range={counter['range']!r} 不合法")
    if counter.get("voice") not in COUNTER_VOICES:
        raise ValueError(
            f"counter.voice={counter.get('voice')!r} 不合法，"
            f"只能是 {' / '.join(COUNTER_VOICES)}"
            f"（low = 压在主旋律下面回话，high = 抬到上面做上方对位）"
        )
    if not 1 <= int(counter["velocity"]) <= 127:
        raise ValueError(f"counter.velocity={counter['velocity']!r} 应在 1~127")
    for item in counter["rhythm"]:
        if len(item) != 3:
            raise ValueError(
                f"counter.rhythm 每项应为 (起始拍, 时长拍, 音级)，收到 {item!r}"
            )
        if not 0 <= int(item[2]) <= 3:
            raise ValueError(
                f"counter.rhythm 的音级 {item[2]!r} 越界，只能是 0~3（和弦内第 1~4 个音）"
            )

    pad = spec["pad"]
    if not 0 < float(pad.get("duck", 1.0)) <= 1:
        raise ValueError(f"pad.duck={pad.get('duck')!r} 应在 (0, 1] 之间（有旋律时压低的比例）")

    perc = spec["perc"]
    if perc["gm"] not in GM_DRUM:
        raise ValueError(f"perc.gm={perc['gm']!r} 不是已知鼓件")
    if not 0 < float(perc["step"]) <= 4:
        raise ValueError(f"perc.step={perc['step']!r} 应在 (0, 4] 拍")
    if not 1 <= int(perc["velocity"]) <= 127:
        raise ValueError(f"perc.velocity={perc['velocity']!r} 应在 1~127")

    arp = spec["arp"]
    low, high = arp["range"]
    if not low < high:
        raise ValueError(f"arp.range={arp['range']!r} 不合法")
    if not 0 < float(arp["step"]) <= 4:
        raise ValueError(f"arp.step={arp['step']!r} 应在 (0, 4] 拍")
    if int(arp.get("octaves", 2)) < 1:
        raise ValueError(f"arp.octaves={arp.get('octaves')!r} 至少为 1")

    humanize = spec["humanize"]
    if not isinstance(humanize, dict) or set(humanize) - {"velocity", "sway"}:
        raise ValueError(f"humanize 应为 dict(velocity=整数, sway=秒)，收到 {humanize!r}")
    if not 0 <= float(humanize.get("sway", 0)) <= 0.03:
        raise ValueError(f"humanize.sway={humanize.get('sway')!r} 太大，建议 0.002~0.015")


def names():
    return tuple(STYLES)
