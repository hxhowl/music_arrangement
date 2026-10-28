"""配置加载与校验。

参数优先级：projects/<dir>/config.json > DEFAULT_CONFIG。

为什么必须下沉到项目目录：全局 config 会让「每首歌独立目录」形同虚设 ——
做第二首歌改一次 BPM，上一版的 .mid 就再也生成不出来了。
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DEFAULT_CONFIG = {
    "bpm": 84,
    "key": "F#m",              # 仅记录用途（report / brief 展示）；和弦由 theory.PROGRESSION 决定
    "time_sig": (4, 4),
    "sections": {
        "intro": 4,
        "verse": 8,
        "chorus": 8,
        "outro": 4,
    },
    "swing": 0.0,              # 尚未实现，必须为 0（见 _validate）
    "velocity_base": 80,       # 主控力度：80 = 基准值，整体按此比例缩放
}


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
        cfg.update(override)
    else:
        print(f"[warn] 未找到 {path}，本版使用默认参数；"
              f"换歌时会互相影响，建议为该项目建一份 config.json")

    if isinstance(cfg["time_sig"], (list, tuple)):
        cfg["time_sig"] = tuple(cfg["time_sig"])

    _validate(cfg)
    return cfg


def _validate(cfg: dict) -> None:
    num, den = cfg["time_sig"]
    if (num, den) != (4, 4):
        # patterns 里 bar_len 是硬编码的 4 拍，写 3/4 而不改 patterns 会得到错位结果
        raise NotImplementedError(
            f"patterns 目前只实现 4/4，config 里是 {num}/{den}；请先改 patterns 或改回 4/4"
        )

    if float(cfg.get("swing", 0.0)) != 0.0:
        raise NotImplementedError(
            "swing 尚未实现（patterns 没有应用 groove 偏移），请保持 0.0，"
            "不要在 config 里写一个不生效的数值"
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
