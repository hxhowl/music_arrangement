"""配置加载与校验。

参数优先级：projects/<dir>/config.json > DEFAULT_CONFIG。

为什么必须下沉到项目目录：全局 config 会让「每首歌独立目录」形同虚设 ——
做第二首歌改一次 BPM，上一版的 .mid 就再也生成不出来了。
和弦进行同理：它现在放在 config 里（key + progression 级数），不再是全局常量。
"""

import json
import os

from core.styles import STYLES
from core.theory import build_progression, default_progression, parse_key

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DEFAULT_CONFIG = {
    "bpm": 84,
    "key": "F#m",                     # 调性：决定和弦的实际音高
    "style": "cinematic",             # 风格：决定律动与织体
    "time_sig": (4, 4),
    "sections": {
        "intro": 4,
        "verse": 8,
        "chorus": 8,
        "outro": 4,
    },
    "velocity_base": 80,              # 主控力度：80 = 基准值，整体按此比例缩放
}
# 注意：progression 不在默认值里 —— 它由 key 的调式决定
# （小调 i-VI-III-VII / 大调 I-V-vi-IV），写死会在换调时算出怪和弦。


def load_config(project_dir: str) -> dict:
    """读项目内 config.json，缺省回退默认值；读不到会明确告警。"""
    cfg = dict(DEFAULT_CONFIG)
    cfg["sections"] = dict(DEFAULT_CONFIG["sections"])

    path = os.path.join(project_dir, "config.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            override = json.load(f)
        if not isinstance(override, dict):
            raise ValueError(f"{path} 顶层必须是 JSON 对象")
        # sections 整体覆盖而不是合并，避免残留上一首歌的段落
        if "sections" in override:
            cfg["sections"] = dict(override.pop("sections"))
        # progression 同理，整条替换
        if "progression" in override:
            cfg["progression"] = list(override.pop("progression"))
        cfg.update(override)
    else:
        print(f"[warn] 未找到 {path}，本版使用默认参数；"
              f"换歌时会互相影响，建议为该项目建一份 config.json")

    # 没写 progression 就按调式给默认进行（小调 i-VI-III-VII / 大调 I-V-vi-IV）
    if not cfg.get("progression"):
        cfg["progression"] = default_progression(cfg["key"])

    if isinstance(cfg["time_sig"], (list, tuple)):
        cfg["time_sig"] = tuple(cfg["time_sig"])

    _validate(cfg)
    return cfg


def _validate(cfg: dict) -> None:
    num, den = cfg["time_sig"]
    if (num, den) != (4, 4):
        # patterns 里按 4 拍一小节推进，写 3/4 而不改 patterns 会得到错位结果
        raise NotImplementedError(
            f"patterns 目前只实现 4/4，config 里是 {num}/{den}；请先改 patterns 或改回 4/4"
        )

    if not cfg["sections"]:
        raise ValueError("config.sections 不能为空")

    for name, bars in cfg["sections"].items():
        if not isinstance(bars, int) or bars <= 0:
            raise ValueError(f"段落 {name!r} 的小节数必须是正整数，当前 {bars!r}")

    if not 20 <= int(cfg["bpm"]) <= 300:
        raise ValueError(f"bpm={cfg['bpm']} 不合理（应在 20~300）")

    if not 1 <= int(cfg.get("velocity_base", 80)) <= 127:
        raise ValueError(f"velocity_base={cfg.get('velocity_base')} 应在 1~127")

    if cfg["style"] not in STYLES:
        raise ValueError(
            f"未知风格 {cfg['style']!r}：可选 {', '.join(STYLES)}（定义在 music/core/styles.py）"
        )

    # 提前算一遍和弦，把 key / progression 的错法在生成前就暴露出来
    parse_key(cfg["key"])
    build_progression(cfg["key"], cfg["progression"])

    if cfg.get("swing", 0.0):
        raise NotImplementedError(
            "swing 尚未实现（patterns 没有应用 groove 偏移），请去掉这个字段"
        )
