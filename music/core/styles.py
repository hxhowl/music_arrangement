"""风格库。

每套风格只描述「怎么演奏」，不决定「哪一段出声」——那是 arrange.py 的事。
所以同一份 ARRANGE（intro 没鼓 / verse 中等 / chorus 满）在不同风格下会得到
完全不同的鼓组，这正是"同一句话换风格 = 另一首歌"的关键。

数据结构：
  chords : octave / hold(占小节比例) / velocity
  bass   : octave / low / high / velocity / rhythm=[(起始拍, 时长拍, accent, 半音偏移)]
  drums  : {密度档: [(GM键名, 起始拍, 时长拍, 基准力度)]}
  lead   : target(中心音区) / breath_every(每 N 小节呼吸一次，0=不呼吸)
           phrases=[[(音级, 起始拍, 时长拍)]]，音级是"和弦内第几个音"
  pad    : octave / intervals / velocity / hold
"""


def _eighths(gm_key: str, base: int, length: float = 0.05):
    """8 分音符，正拍重、反拍轻。"""
    return [(gm_key, i * 0.5, length, base if i % 2 == 0 else int(base * 0.72)) for i in range(8)]


def _quarters(gm_key: str, base: int, length: float = 0.06):
    return [(gm_key, float(i), length, base if i % 2 == 0 else int(base * 0.8)) for i in range(4)]


STYLES = {
    # 电影感：长音铺底、鼓只做心跳、旋律大跳
    "cinematic": dict(
        chords=dict(octave=3, hold=0.99, velocity=46),
        bass=dict(octave=1, low=33, high=44, velocity=74,
                  rhythm=[(0.0, 3.9, 1.0, 0)]),
        drums={
            "light":  [("kick", 0.0, 0.25, 52)],
            "medium": [("kick", 0.0, 0.25, 72), ("kick", 1.75, 0.2, 44)],
            "full":   [("kick", 0.0, 0.25, 96), ("kick", 2.0, 0.25, 84),
                       ("snare", 2.0, 0.22, 66), ("tom_low", 3.75, 0.3, 58)],
        },
        lead=dict(target=69, breath_every=0,
                  phrases=[[(0, 0.0, 1.9), (2, 2.0, 1.9)]]),
        pad=dict(octave=3, intervals=(12, 19, 24), velocity=42, hold=1.0),
    ),

    # 流行：标准 4/4，贝斯八分推进到五度
    "pop": dict(
        chords=dict(octave=3, hold=0.88, velocity=58),
        bass=dict(octave=1, low=33, high=44, velocity=88,
                  rhythm=[(0.0, 0.45, 1.0, 0), (1.0, 0.45, 0.85, 0),
                          (2.0, 0.45, 1.0, 0), (2.5, 0.4, 0.75, 7),
                          (3.0, 0.45, 0.85, 0)]),
        drums={
            "light":  [("kick", 0.0, 0.1, 72)] + _eighths("hat", 34),
            "medium": [("kick", 0.0, 0.1, 88), ("snare", 2.0, 0.1, 74)] + _eighths("hat", 40),
            "full":   [("kick", 0.0, 0.1, 105), ("kick", 1.5, 0.1, 78),
                       ("kick", 2.0, 0.1, 95), ("kick", 2.75, 0.08, 62),
                       ("snare", 1.0, 0.1, 90), ("snare", 3.0, 0.1, 92)] + _eighths("hat", 46),
        },
        lead=dict(target=69, breath_every=4,
                  phrases=[
                      [(0, 0.0, 0.8), (1, 1.0, 0.8), (2, 2.0, 0.8), (1, 3.0, 0.8)],
                      [(0, 0.0, 0.8), (2, 1.0, 0.8), (3, 2.0, 0.8), (2, 3.0, 0.8)],
                  ]),
        pad=dict(octave=3, intervals=(12, 16, 19), velocity=34, hold=0.98),
    ),

    # 慵懒：切分贝斯、半拍鼓、短句重复
    "lofi": dict(
        chords=dict(octave=3, hold=0.72, velocity=52),
        bass=dict(octave=1, low=33, high=44, velocity=80,
                  rhythm=[(0.0, 0.7, 1.0, 0), (0.75, 0.4, 0.6, 0),
                          (1.5, 0.5, 0.85, 0), (2.5, 0.6, 0.9, 7)]),
        drums={
            "light":  [("kick", 0.0, 0.1, 54)] + _quarters("hat", 26),
            "medium": [("kick", 0.0, 0.12, 78), ("snare", 2.0, 0.12, 58)]
                      + _eighths("hat", 30),
            "full":   [("kick", 0.0, 0.12, 88), ("kick", 1.75, 0.1, 60),
                       ("snare", 2.0, 0.12, 70)] + _eighths("hat", 36),
        },
        lead=dict(target=69, breath_every=4,
                  phrases=[
                      [(0, 0.0, 0.55), (1, 0.75, 0.45), (1, 1.5, 0.45), (2, 2.5, 0.9)],
                      [(0, 0.0, 0.55), (2, 0.5, 0.45), (1, 1.25, 0.45), (3, 2.5, 0.9)],
                  ]),
        pad=dict(octave=3, intervals=(12, 19), velocity=32, hold=0.92),
    ),

    # 无厘头：断奏和弦、错位重音、大跳旋律
    "playful": dict(
        chords=dict(octave=3, hold=0.35, velocity=66),
        # 贝斯音区比其它风格低一个窗口：这套律动有 +12 的八度跳，
        # 窗口太高会把贝斯顶到 G3，和 chords 轨撞在一起
        bass=dict(octave=1, low=26, high=38, velocity=92,
                  rhythm=[(0.0, 0.35, 1.0, 0), (0.5, 0.35, 0.55, 12),
                          (2.0, 0.35, 1.0, 0), (2.75, 0.5, 0.7, 7)]),
        drums={
            "light":  [("kick", 0.0, 0.1, 70), ("hat", 2.0, 0.05, 48)],
            "medium": [("kick", 0.0, 0.1, 92), ("snare", 2.5, 0.1, 70)]
                      + _eighths("hat", 42),
            "full":   [("kick", 0.0, 0.1, 108), ("kick", 1.5, 0.1, 86),
                       ("snare", 1.0, 0.1, 95), ("snare", 3.0, 0.1, 98),
                       ("tom_high", 3.5, 0.1, 78)] + _eighths("hat", 48),
        },
        lead=dict(target=72, breath_every=4,
                  phrases=[
                      [(0, 0.0, 0.4), (2, 0.5, 0.4), (1, 1.0, 0.4),
                       (3, 2.0, 0.4), (2, 2.5, 0.4)],
                      [(3, 0.0, 0.4), (1, 0.5, 0.4), (0, 1.0, 0.6), (2, 2.5, 0.8)],
                  ]),
        pad=dict(octave=3, intervals=(12, 19, 24), velocity=28, hold=0.9),
    ),
}


def get(name: str) -> dict:
    if name not in STYLES:
        raise KeyError(f"未知风格 {name!r}：可选 {', '.join(STYLES)}")
    return STYLES[name]


def names():
    return tuple(STYLES)
