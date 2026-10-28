import random
from dataclasses import dataclass


@dataclass
class Ctx:
    """一次 build 调用需要的全部上下文。

    把 bpm / 段落位置 / 和弦进行 / 风格 / 力度 / 随机源一次性传下去，
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
    style_spec: dict           # 已叠加 style_tweaks 的风格参数（只读，不要改）
    density: str | None = None  # 鼓密度档：None / light / medium / full
    crash: bool = False         # 段落起点是否加吊镲
    fill: bool = True           # 是否每 4 小节加过门
    seed: int = 0
    rng: random.Random | None = None   # seed=0 时为 None，输出完全确定

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

    def jitter(self, velocity: int, spread: int = 4) -> int:
        """力度微扰动。seed=0 时原样返回，保证同参数可复现。"""
        if self.rng is None:
            return max(1, min(127, int(velocity)))
        return max(1, min(127, int(velocity) + self.rng.randint(-spread, spread)))

    def chance(self, probability: float) -> bool:
        """按概率决定是否加装饰音。seed=0 时永远为 False。"""
        return self.rng is not None and self.rng.random() < probability

    def pick(self, options):
        """从多个变体里挑一个。seed=0 时固定取第一个。"""
        if self.rng is None:
            return options[0]
        return options[self.rng.randrange(len(options))]
