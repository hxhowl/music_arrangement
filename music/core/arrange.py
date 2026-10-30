"""段落编排矩阵。

每个 section 决定：哪些轨出声、鼓打到什么密度、整体力度、要不要吊镲/过门，
以及**这一段用哪套风格**（留空 = 用整首歌的 style）。

注意分工：这里只决定"这一段怎么排"，"这个密度具体怎么打"由 styles.py 决定。
所以同一份 ARRANGE 在 cinematic 下是心跳、在 pop 下是标准 4/4、在 playful 下是错位重音。

出厂默认在下面，项目要覆盖就用 config.json 的 arrange，**不要改这个文件** ——
改了等于改所有项目，违反"每次改动只作用于当前这首歌"。
"""

from core.styles import COUNTER_VOICES, STYLES

TRACK_KEYS = ("chords", "bass", "drums", "perc", "arp", "lead", "counter", "pad")
DRUM_LEVELS = (None, "light", "medium", "full")
# 渐强/渐弱在这条阶梯上插值：往上走到本段密度，或从本段密度往下走一档
DRUM_LADDER = (None, "light", "medium", "full")
# build: None=整段一个密度；"up"=段内从低一档爬到本段密度；"down"=反过来
BUILD_MODES = (None, "up", "down")

# drums: None=不出鼓 / "light" / "medium" / "full"
# style: None=用整首歌的 style；也可写 "playful" 让这一段换风格
# crash: 段落起点是否加吊镲；fill: 是否按 fill_every 加过门
# counter: 副旋律。默认只在主歌/桥段开 —— 副歌要把空间留给主旋律，
#          而且副旋律只在主旋律空着的地方出声，主歌没旋律时它才有位置。
#          想在副歌也加，就写 config.arrange.chorus.counter = true。
# counter_voice: 副旋律在哪一侧。None = 用风格里的 voice；
#          "low" = 压在主旋律下面当回话，"high" = 抬到上面做上方对位。
#          典型用法：副歌把 counter 打开并设成 "high"，马上多一层。
ARRANGE = {
    "intro":  dict(chords=True, bass=False, drums=None,     perc=False, arp=True,
                   lead=False, counter=False, pad=True,
                   vel=0.70, crash=False, fill=False, style=None, counter_voice=None, build=None),
    "verse":  dict(chords=True, bass=True,  drums="medium", perc=True,  arp=False,
                   lead=False, counter=True,  pad=True,
                   vel=0.85, crash=False, fill=True,  style=None, counter_voice=None, build=None),
    "chorus": dict(chords=True, bass=True,  drums="full",   perc=True,  arp=True,
                   lead=True,  counter=False, pad=True,
                   vel=1.00, crash=True,  fill=True,  style=None, counter_voice=None,
                   build="up"),
    "bridge": dict(chords=True, bass=True,  drums="light",  perc=False, arp=True,
                   lead=False, counter=True,  pad=True,
                   vel=0.80, crash=False, fill=True,  style=None, counter_voice=None, build=None),
    "outro":  dict(chords=True, bass=False, drums=None,     perc=False, arp=False,
                   lead=False, counter=False, pad=True,
                   vel=0.65, crash=False, fill=False, style=None, counter_voice=None, build=None),
}


def get(section: str, overrides: dict = None) -> dict:
    """取段落编排，允许项目内覆盖；未定义段落直接报错（不要静默跳过整段）。

    overrides 形如 {"chorus": {"drums": "medium", "style": "playful"}}，
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
    for flag in ("crash", "fill", "perc", "arp", "counter"):
        if not isinstance(arr[flag], bool):
            raise ValueError(f"段落 {section!r} 的 {flag}={arr[flag]!r} 必须是 true/false")
    if arr["style"] is not None and arr["style"] not in STYLES:
        raise ValueError(
            f"段落 {section!r} 的 style={arr['style']!r} 未知，"
            f"可选 {', '.join(STYLES)}（或留空表示跟整首歌）"
        )
    if arr["counter_voice"] is not None and arr["counter_voice"] not in COUNTER_VOICES:
        raise ValueError(
            f"段落 {section!r} 的 counter_voice={arr['counter_voice']!r} 不合法，"
            f"只能是 {' / '.join(COUNTER_VOICES)}（或留空表示用风格里的设置）"
        )
    if arr["build"] not in BUILD_MODES:
        raise ValueError(
            f"段落 {section!r} 的 build={arr['build']!r} 不合法，"
            f"只能是 null / \"up\" / \"down\"（up = 段内渐强，down = 渐弱）"
        )
    try:
        arr["vel"] = float(arr["vel"])
    except (TypeError, ValueError):
        raise ValueError(f"段落 {section!r} 的 vel={arr['vel']!r} 不是数字")
    if not 0 < arr["vel"] <= 2:
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


def section_styles(sections, overrides: dict = None) -> dict:
    """每段实际使用的风格名（None 表示跟整首歌）；供输出提示用。"""
    return {section: get(section, overrides)["style"] for section in sections}
