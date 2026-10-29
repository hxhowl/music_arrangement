"""乐器选择：给 8 个功能槽配"默认推荐乐器"，并允许按项目换。

设计前提（重要）：**MIDI 里没有"乐器"这个概念。** 我们能控制的只有三样东西：

  1. GM program 号 —— 导入 Logic 时给它一个"该加载什么音源"的提示
  2. 演奏法微调 —— 真的改变 MIDI 音符（弦乐把长音拉满、吉他把和弦变短）
  3. 你自己在 Logic 里加载什么 —— 代码管不到，只能建议

所以这里每条乐器都带 `tweaks`：换乐器时顺手把**弹法**调到不离谱。
没有这一步，"换成弦乐群"就只是换了个 program 号，音符还是一个断一个断的 ——
上一轮讨论过的"换音色不换弹法"。

优先级：风格默认 < 乐器自带 tweaks < config.style_tweaks（显式最优先）。
"""

from core.theory import GM_DRUM  # noqa: F401  （perc 选项要用到鼓件名）

# 每个功能槽可选的乐器。program 是 GM 编号（0~127）；drums 用 GM 鼓组编号。
# why 是给用户看的一句话建议，会原样出现在 `bash tools/instruments.sh` 的输出里。
#
# 例外：perc 不写 program。它和 drums 共用 MIDI 通道 10（GM 规定鼓组只能在通道 10，
# 且同一通道同一时刻只能有一个鼓组），所以 perc 的鼓组由 drums 决定 ——
# 见下面的 KIT_SHARED。perc 真正能选的是**打哪个鼓件**（gm=shaker/clap/...）。
INSTRUMENTS = {
    "chords": {
        "piano":    dict(program=0,  name="原声钢琴", why="通用，柱式和弦最贴它的性格"),
        "epiano":   dict(program=4,  name="电钢琴",   why="lofi / 流行，柔和不抢人声"),
        "nylon":    dict(program=24, name="尼龙弦吉他", why="⚠️ 民谣、亲子；柱式和弦略假，需要扫弦/把位才像",
                         tweaks={"chords": {"hold": 0.66}}),
        "steel":    dict(program=25, name="钢弦吉他", why="⚠️ 流行扫弦；缺扫弦时序，只适合当铺底",
                         tweaks={"chords": {"hold": 0.6}}),
        "strings":  dict(program=48, name="弦乐群",   why="电影感首选，长音连起来才像弦乐",
                         tweaks={"chords": {"hold": 0.99}}),
        "organ":    dict(program=16, name="拉杆风琴", why="复古、福音，铺满不换气",
                         tweaks={"chords": {"hold": 0.98}}),
    },
    "bass": {
        "finger":   dict(program=33, name="指弹电贝斯", why="通用，最不容易出错"),
        "pick":     dict(program=34, name="拨片电贝斯", why="摇滚 / 流行，更硬更亮"),
        "upright":  dict(program=32, name="立式贝斯",   why="jazz / lofi / 民谣，木头味"),
        "synth":    dict(program=38, name="合成贝斯",   why="电子 / 短视频，低频更整齐"),
    },
    "drums": {
        "standard": dict(program=0,  name="标准鼓组",   why="万能"),
        "room":     dict(program=8,  name="Room 鼓组",  why="比标准更自然，像在小房间录的"),
        "power":    dict(program=16, name="Power 鼓组", why="摇滚，底鼓军鼓更重"),
        "electronic": dict(program=24, name="电子鼓组", why="短视频 / 电子，808 感"),
        "brush":    dict(program=40, name="刷子鼓组",   why="lofi / jazz，柔软不抢戏"),
    },
    "perc": {
        "shaker":     dict(name="沙锤",  why="最百搭，不占低频",
                           tweaks={"perc": {"gm": "shaker"}}),
        "tambourine": dict(name="铃鼓",  why="流行 / 欢快，正拍更亮",
                           tweaks={"perc": {"gm": "tambourine"}}),
        "rim":        dict(name="鼓边侧击", why="无厘头 / 错位感",
                           tweaks={"perc": {"gm": "rim"}}),
        "congas":     dict(name="康加鼓", why="拉丁 / 亲子，有手鼓味",
                           tweaks={"perc": {"gm": "conga"}}),
        "clap":       dict(name="拍手",  why="短视频常用，强调 2、4 拍",
                           tweaks={"perc": {"gm": "clap"}}),
    },
    "arp": {
        "pluck":    dict(program=45, name="拨弦（pizzicato）", why="比合成器更像真乐器",
                         tweaks={"arp": {"step": 0.5}}),
        "harp":     dict(program=46, name="竖琴",   why="亲子 / 童话，颗粒清楚",
                         tweaks={"arp": {"step": 0.5}}),
        "marimba":  dict(program=12, name="马林巴", why="温暖、有木质，lofi 好用",
                         tweaks={"arp": {"step": 0.5}}),
        "synth":    dict(program=81, name="合成琶音", why="电子 / 流行，中高频更亮"),
        "glocken":  dict(program=9,  name="音铃",   why="点缀，少用，容易刺耳"),
    },
    "lead": {
        "synth_lead": dict(program=80, name="方波主音", why="通用合成主音，中性"),
        "flute":      dict(program=73, name="长笛",   why="亲子 / 民谣，柔、不刺",
                           tweaks={"lead": {"breath_every": 2}}),
        "violin":     dict(program=40, name="小提琴", why="⚠️ 电影感；需要连弓与揉弦，长音才像",
                           tweaks={"lead": {"breath_every": 0}}),
        "sax":        dict(program=65, name="中音萨克斯", why="⚠️ 爵士 / 都市；缺弯音，会偏「直」",
                           tweaks={"lead": {"breath_every": 4}}),
        "harmonica":  dict(program=22, name="口琴",   why="⚠️ 公路 / 怀旧；辨识度极高，容易露馅",
                           tweaks={"lead": {"breath_every": 4}}),
        "whistle":    dict(program=78, name="哨笛",   why="亲子 / 田园，高频亮但不需要力度"),
    },
    "counter": {
        "cello":       dict(program=42, name="大提琴", why="最稳的副旋律音色，低音区有厚度"),
        "viola":       dict(program=41, name="中提琴", why="比大提琴亮一点，别和 lead 撞"),
        "french_horn": dict(program=60, name="圆号",   why="电影感，长音很稳"),
        "bassoon":     dict(program=70, name="巴松",   why="低音木管，比大提琴更「干」"),
    },
    "pad": {
        "polysynth": dict(program=90, name="合成铺底", why="中性，什么都不冲突"),
        "warm":      dict(program=89, name="暖 Pad", why="比 polysynth 柔，适合 lofi"),
        "strings":   dict(program=48, name="弦乐群", why="电影感首选，长音连起来",
                          tweaks={"pad": {"hold": 0.99, "duck": 0.7}}),
        "choir":     dict(program=52, name="人声合唱", why="圣洁 / 空灵；会占中频，要压低",
                          tweaks={"pad": {"velocity": 28}}),
        "church":    dict(program=19, name="教堂风琴", why="庄严，低频厚，慎用"),
    },
}

# 出厂默认：和这套工程历史产物保持一致，老项目不写 instruments 时行为不变
DEFAULT = {
    "chords": "piano",
    "bass": "finger",
    "drums": "standard",
    "perc": "shaker",
    "arp": "synth",
    "lead": "synth_lead",
    "counter": "cello",
    "pad": "polysynth",
}

# 编制预设：一次配好 8 个槽，适合"我要一个流行乐队 / 一个电影感编制"
PRESETS = {
    "band": {
        "chords": "epiano", "bass": "finger", "drums": "standard",
        "perc": "tambourine", "arp": "pluck", "lead": "synth_lead",
        "counter": "cello", "pad": "warm",
    },
    "cinematic": {
        "chords": "strings", "bass": "upright", "drums": "room",
        "perc": "shaker", "arp": "harp", "lead": "violin",
        "counter": "french_horn", "pad": "strings",
    },
    "lofi": {
        "chords": "epiano", "bass": "upright", "drums": "brush",
        "perc": "shaker", "arp": "marimba", "lead": "flute",
        "counter": "cello", "pad": "warm",
    },
    "acoustic": {
        "chords": "nylon", "bass": "upright", "drums": "brush",
        "perc": "congas", "arp": "harp", "lead": "flute",
        "counter": "cello", "pad": "strings",
    },
    "electronic": {
        "chords": "epiano", "bass": "synth", "drums": "electronic",
        "perc": "clap", "arp": "synth", "lead": "synth_lead",
        "counter": "cello", "pad": "polysynth",
    },
}

# 新项目按风格自动带的预设（"默认推荐乐器"的落地方式）
STYLE_PRESET = {
    "cinematic": "cinematic",
    "pop": "band",
    "lofi": "lofi",
    "playful": "band",
}

# 共用鼓组的槽：{跟随者: 决定鼓组的槽}。跟随者自己不带 program，
# 由 plan() 填成 leader 的鼓组号 —— 两条轨写同一个号，才不会在通道 10 上互相覆盖。
KIT_SHARED = {"perc": "drums"}

SLOTS = tuple(INSTRUMENTS)


def _check_registry() -> None:
    """注册表自检：写错一个 program 号或 tweaks 分组，这里就该炸。"""
    from core.arrange import TRACK_KEYS

    if set(INSTRUMENTS) != set(TRACK_KEYS):
        raise RuntimeError(
            f"instruments.INSTRUMENTS 的槽与 TRACK_KEYS 不一致："
            f"{sorted(set(INSTRUMENTS) ^ set(TRACK_KEYS))}"
        )

    for slot, options in INSTRUMENTS.items():
        for key, entry in options.items():
            if slot in KIT_SHARED:
                if "program" in entry:
                    raise RuntimeError(
                        f"{slot}.{key} 不该自带 program：鼓组由 {KIT_SHARED[slot]} 决定"
                    )
            elif not 0 <= int(entry.get("program", -1)) <= 127:
                raise RuntimeError(f"{slot}.{key} 的 program={entry.get('program')} 越界")
            if not entry.get("name") or not entry.get("why"):
                raise RuntimeError(f"{slot}.{key} 缺 name 或 why")
            for group in (entry.get("tweaks") or {}):
                if group not in TRACK_KEYS:
                    raise RuntimeError(f"{slot}.{key} 的 tweaks 指向未知分组 {group!r}")

    for slot, leader in KIT_SHARED.items():
        if leader not in INSTRUMENTS:
            raise RuntimeError(f"KIT_SHARED[{slot!r}]={leader!r} 不是已知槽")

    for slot, key in DEFAULT.items():
        if key not in INSTRUMENTS[slot]:
            raise RuntimeError(f"DEFAULT[{slot!r}]={key!r} 不在可选列表里")

    for preset, mapping in PRESETS.items():
        for slot, key in mapping.items():
            if slot not in INSTRUMENTS:
                raise RuntimeError(f"预设 {preset!r} 里有未知槽 {slot!r}")
            if key not in INSTRUMENTS[slot]:
                raise RuntimeError(f"预设 {preset!r} 的 {slot}={key!r} 不在可选列表里")

    for style, preset in STYLE_PRESET.items():
        if preset not in PRESETS:
            raise RuntimeError(f"STYLE_PRESET[{style!r}]={preset!r} 不存在")


_check_registry()


def options(slot: str):
    """某个槽的可选乐器名（供报错信息和 --list 用）。"""
    if slot not in INSTRUMENTS:
        raise KeyError(f"未知功能槽 {slot!r}：可用 {', '.join(SLOTS)}")
    return tuple(INSTRUMENTS[slot])


def get(slot: str, key: str) -> dict:
    """取某个槽的具体乐器；写错就报错并列出可选项。"""
    if slot not in INSTRUMENTS:
        raise KeyError(f"未知功能槽 {slot!r}：可用 {', '.join(SLOTS)}")
    if key not in INSTRUMENTS[slot]:
        raise KeyError(
            f"{slot} 没有 {key!r} 这个乐器：可用 {', '.join(INSTRUMENTS[slot])}"
        )
    return INSTRUMENTS[slot][key]


def plan(cfg: dict) -> dict:
    """算出这首歌每个槽实际用什么。

    优先级：DEFAULT < preset < config.instruments（后者最具体，优先级最高）
    """
    chosen = dict(DEFAULT)

    preset_name = cfg.get("preset")
    if preset_name:
        if preset_name not in PRESETS:
            raise ValueError(
                f"未知编制预设 {preset_name!r}：可用 {', '.join(PRESETS)}"
            )
        chosen.update(PRESETS[preset_name])

    override = cfg.get("instruments") or {}
    if not isinstance(override, dict):
        raise ValueError("config.instruments 必须是对象，如 {\"chords\": \"nylon\"}")
    unknown = set(override) - set(INSTRUMENTS)
    if unknown:
        raise ValueError(
            f"config.instruments 里有未知功能槽 {sorted(unknown)}，"
            f"可用 {', '.join(SLOTS)}"
        )
    for slot, key in override.items():
        get(slot, key)          # 校验，错误信息里会列出该槽可选值
        chosen[slot] = key

    resolved = {slot: dict(key=key, **get(slot, key)) for slot, key in chosen.items()}

    # 共用鼓组：跟随者复制 leader 的鼓组号，两条轨在通道 10 上写同一个值
    for slot, leader in KIT_SHARED.items():
        resolved[slot]["program"] = resolved[leader]["program"]

    return resolved


def tweaks_of(plan_map: dict) -> dict:
    """汇总所有乐器自带的演奏法微调，形如 {"pad": {"hold": 0.99}}。"""
    out = {}
    for entry in plan_map.values():
        for group, patch in (entry.get("tweaks") or {}).items():
            out.setdefault(group, {}).update(patch)
    return out


def merge_tweaks(base: dict, extra: dict) -> dict:
    """extra 打底，base 覆盖（显式配置优先）。"""
    out = {k: (dict(v) if isinstance(v, dict) else v) for k, v in (extra or {}).items()}
    for group, patch in (base or {}).items():
        if isinstance(patch, dict) and isinstance(out.get(group), dict):
            out[group] = {**out[group], **patch}
        else:
            out[group] = patch
    return out


def describe(plan_map: dict) -> str:
    """一行摘要，写进 compose 的输出。"""
    return "  ".join(
        f"{slot}={entry['name']}" for slot, entry in plan_map.items()
    )
