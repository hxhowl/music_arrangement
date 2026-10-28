from dataclasses import dataclass


@dataclass
class Ctx:
    """一次 build 调用需要的全部上下文。

    把 bpm / 段落位置 / 和弦进行 / 风格 / 力度一次性传下去，
    pattern 就不用满世界 import 全局变量了（旧版直接 import PROGRESSION，
    导致换歌必须改全局，是"创作隔离"漏掉的那一环）。
    """

    bpm: float
    start_bar: int
    bars: int
    progression: list          # 实际和弦名，按小节循环，如 ["F#m","D","A","E"]
    chords: dict               # 和弦名 -> 相对根音的半音列表
    vel_scale: float
    style: str
    density: str | None = None  # 鼓密度档：None / light / medium / full
    crash: bool = False         # 段落起点是否加吊镲
    fill: bool = True           # 是否每 4 小节加过门

    @property
    def beat(self) -> float:
        return 60.0 / self.bpm

    @property
    def bar_len(self) -> float:
        return 4 * self.beat

    def chord_at(self, index: int) -> str:
        return self.progression[index % len(self.progression)]

    def bar_time(self, index: int) -> float:
        return (self.start_bar + index) * self.bar_len
