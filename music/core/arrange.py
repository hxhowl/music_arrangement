"""段落编排矩阵。

每个 section 决定：哪些轨出声、鼓打到什么密度、整体力度缩放多少。

注意分工：**这里只决定"哪一段出声、多稀多密"（light/medium/full），
"这个密度具体怎么打"由 styles.py 决定**。所以同一份 ARRANGE 在
cinematic 下是心跳、在 pop 下是标准 4/4、在 playful 下是错位重音。

旧实现用 `if section in ("intro","verse","chorus")` 白名单，在 config 里加
`"bridge"` 会**静默丢弃整段**。现在改成查表，查不到直接报错（fail loud）。
"""

TRACK_KEYS = ("chords", "bass", "drums", "lead", "pad")
DRUM_LEVELS = (None, "light", "medium", "full")

# 出厂默认编排。**项目要调就用 config.json 的 arrange 覆盖，不要改这里** ——
# 改这里等于改所有项目，违反「每次改动只作用于当前这首歌」。
# drums: None=不出鼓 / "light" / "medium" / "full"
ARRANGE = {
    "intro":  dict(chords=True, bass=False, drums=None,     lead=False, pad=True,  vel=0.70),
    "verse":  dict(chords=True, bass=True,  drums="medium", lead=False, pad=True,  vel=0.85),
    "chorus": dict(chords=True, bass=True,  drums="full",   lead=True,  pad=True,  vel=1.00),
    "bridge": dict(chords=True, bass=True,  drums="light",  lead=False, pad=True,  vel=0.80),
    "outro":  dict(chords=True, bass=False, drums=None,     lead=False, pad=True,  vel=0.65),
}


def get(section: str, overrides: dict = None) -> dict:
    """取段落编排，允许项目内覆盖；未定义段落直接报错（不要静默跳过整段）。

    overrides 形如 {"chorus": {"drums": "medium", "vel": 0.9}}，
    只覆盖给出的键，其余沿用默认值。
    """
    if section not in ARRANGE:
        raise KeyError(
            f"未知段落 {section!r}：请先在 music/core/arrange.py 的 ARRANGE 中定义"
            f"（已支持: {', '.join(ARRANGE)}）"
        )

    arr = dict(ARRANGE[section])
    if not overrides:
        return arr

    patch = overrides.get(section)
    if patch is None:
        return arr
    if not isinstance(patch, dict):
        raise ValueError(f"config.arrange[{section!r}] 必须是对象，收到 {type(patch).__name__}")

    unknown = set(patch) - set(arr)
    if unknown:
        raise ValueError(
            f"config.arrange[{section!r}] 里有未知字段 {sorted(unknown)}，"
            f"可用：{', '.join(arr)}"
        )

    arr.update(patch)
    if arr["drums"] not in DRUM_LEVELS:
        raise ValueError(
            f"段落 {section!r} 的 drums={arr['drums']!r} 不合法，"
            f"只能是 None / light / medium / full"
        )
    if not 0 < float(arr["vel"]) <= 2:
        raise ValueError(f"段落 {section!r} 的 vel={arr['vel']} 应在 (0, 2] 之间")
    return arr


def validate_overrides(overrides) -> None:
    """提前校验 config.arrange，别等生成到一半才炸。"""
    if overrides is None:
        return
    if not isinstance(overrides, dict):
        raise ValueError("config.arrange 必须是对象")
    for section in overrides:
        get(section, overrides)


def active_tracks(sections, overrides: dict = None) -> set:
    """给定 section 顺序，算出本曲会出现音符的轨（供产物体检对比）。"""
    return {
        key
        for section in sections
        for key in TRACK_KEYS
        if get(section, overrides).get(key)
    }
