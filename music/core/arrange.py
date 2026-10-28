"""段落编排矩阵。

每个 section 决定：哪些轨出声、鼓打到什么密度、整体力度缩放多少。

旧实现用 `if section in ("intro","verse","chorus")` 白名单，在 config 里加
`"bridge"` 会**静默丢弃整段**。现在改成查表，查不到直接报错（fail loud）。
"""

TRACK_KEYS = ("chords", "bass", "drums", "lead", "pad")

# drums 取值见 patterns/drums.py：None=不出鼓 / "hat" / "half" / "full"
ARRANGE = {
    "intro":  dict(chords=True, bass=False, drums=None,   lead=False, pad=True,  vel=0.70),
    "verse":  dict(chords=True, bass=True,  drums="half", lead=False, pad=True,  vel=0.85),
    "chorus": dict(chords=True, bass=True,  drums="full", lead=True,  pad=True,  vel=1.00),
    "bridge": dict(chords=True, bass=True,  drums="hat",  lead=False, pad=True,  vel=0.80),
    "outro":  dict(chords=True, bass=False, drums=None,   lead=False, pad=True,  vel=0.65),
}


def get(section: str) -> dict:
    """取段落编排；未定义则报错（不要静默跳过整段）。"""
    if section not in ARRANGE:
        raise KeyError(
            f"未知段落 {section!r}：请先在 music/core/arrange.py 的 ARRANGE 中定义"
            f"（已支持: {', '.join(ARRANGE)}）"
        )
    return ARRANGE[section]


def active_tracks(sections) -> set:
    """给定 section 顺序，算出本曲会出现音符的轨（供产物体检对比）。"""
    return {
        key
        for section in sections
        for key in TRACK_KEYS
        if get(section).get(key)
    }
