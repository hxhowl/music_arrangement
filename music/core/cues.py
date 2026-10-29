"""音效时间点清单（SFX cue sheet）。

**为什么不生成音效轨**：riser / impact / whoosh / sub-drop 在真实制作里是**采样**，
MIDI 只能触发合成器音色 —— 把它塞成第 8 条轨，得到的是"一段莫名其妙的合成器声"，
不是音效。所以这里产出的是**时间点**：第几小节、第几秒该放什么，
你在 Logic 里拖个采样上去就能用。

规则是按段落编排推的，不是写死某首歌；想加自定义点就写 config 的 `cues`。
"""

import os

# 段落类型 -> 这一段的戏剧功能。名字是固定词汇表（见 arrange.ARRANGE），
# 所以这里按类型给建议是安全的；换了段落名会被 config 校验拦下。
SECTION_ROLE = {
    "intro": "开场",
    "verse": "陈述",
    "chorus": "高潮",
    "bridge": "转折",
    "outro": "收尾",
}


def _mmss(seconds: float) -> str:
    total = max(0, int(round(seconds)))
    return f"{total // 60}:{total % 60:02d}"


def _plan(cfg):
    """按段落推出一串 (小节, 拍, 音效, 理由)。"""
    from core.arrange import get as get_arrange

    overrides = cfg.get("arrange") or {}
    cues = []
    offset = 0
    previous = None

    for section, bars in cfg["sections"].items():
        arr = get_arrange(section, overrides)
        role = SECTION_ROLE.get(section, section)

        if offset > 0:
            reason = f"{role}段进入"
            if previous and previous["drums"] is None and arr["drums"]:
                cues.append((offset, 1, "impact + sub drop", f"{reason}，鼓第一次进来"))
            elif previous and previous["drums"] and arr["drums"] is None:
                cues.append((offset, 1, "reverse cymbal / 抽空", f"{reason}，鼓撤掉，要一个反向效果"))
            else:
                cues.append((offset, 1, "impact（轻）", reason))

            if offset >= 2:
                cues.append((offset - 2, 1, "riser（铺 2 小节渐强）",
                             f"给{role}段做 build-up"))

        if section == "outro":
            cues.append((offset, 1, "downlifter / 尾噪", "收尾，把能量卸掉"))

        previous = arr
        offset += bars

    total = sum(int(v) for v in cfg["sections"].values())
    if total >= 4:
        cues.append((total - 2, 3, "尾部处理", "最后两小节留混响尾巴，别一刀切"))

    # 手动补充：config.cues = [{"bar": 21, "beat": 3, "what": "whoosh", "why": "..."}]
    for extra in cfg.get("cues") or []:
        if not isinstance(extra, dict) or "bar" not in extra:
            raise ValueError(f"config.cues 每项至少要有 bar 字段，收到 {extra!r}")
        bar = int(extra["bar"])
        if not 1 <= bar <= total:
            raise ValueError(f"config.cues 的 bar={bar} 超出范围（1~{total}）")
        cues.append((bar - 1, int(extra.get("beat", 1)),
                     extra.get("what", "自定义音效"), extra.get("why", "手动指定")))

    return sorted(cues, key=lambda c: (c[0], c[1])), total


def write_cues(cfg: dict, out_dir: str, project_name: str, version: str) -> str:
    """写 <name>-<version>.cues.md，返回路径。"""
    cues, total = _plan(cfg)
    bpm = float(cfg["bpm"])
    bar_len = 4 * 60.0 / bpm
    length = total * bar_len

    lines = [
        f"# {project_name}-{version} 音效时间点",
        "",
        f"{bpm:g} BPM · {total} 小节 · {length:.1f} 秒",
        "",
        "这些音效**没有写进 MIDI**：riser / impact / whoosh 是采样，",
        "MIDI 只能触发合成器音色。在 Logic 里按下表放在音频轨上，位置对齐小节即可。",
        "",
        "| 时间 | 小节.拍 | 音效 | 为什么在这里 |",
        "|---|---|---|---|",
    ]
    for bar, beat, what, why in cues:
        seconds = bar * bar_len + (beat - 1) * (60.0 / bpm)
        lines.append(f"| {_mmss(seconds)} | {bar + 1}.{beat} | {what} | {why} |")

    lines += [
        "",
        "## 怎么用",
        "",
        "1. 在 Logic 建一条音频轨（建议命名 `SFX`），把所有采样都放这一条上",
        "2. 每个点用「小节.拍」对位，不要看秒数 —— 改 BPM 时秒数会变，小节不会",
        "3. 音效轨不要和鼓抢低频：impact 的 sub 部分建议高通到 40Hz 以上",
        "4. 想加/改点位：在 `projects/<dir>/config.json` 里写 `cues`，",
        "   格式 `[{{\"bar\": 21, \"beat\": 3, \"what\": \"whoosh\", \"why\": \"副歌前转场\"}}]`",
        "",
    ]

    path = os.path.join(out_dir, f"{project_name}-{version}.cues.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path
