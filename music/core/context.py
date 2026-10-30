import random
from dataclasses import dataclass, field


@dataclass
class Ctx:
    """一次 build 调用需要的全部上下文。

    把 bpm / 段落位置 / 和弦进行 / 风格 / 力度 / 随机源一次性传下去，
    pattern 就不用满世界 import 全局变量了（旧版直接 import PROGRESSION，
    导致换歌必须改全局，是"创作隔离"漏掉的那一环）。

    时间轴的三个维度都在这里统一处理，pattern 不要自己算：
      - 和声节奏：`chord_spans()` 把一小节切成若干和声段（半小节换和弦）
      - swing：`at()` 会把每拍后半拍往后推
      - 随机演奏：`jitter()` / `sway()` / `chance()`
    """

    bpm: float
    start_bar: int
    bars: int
    progression: list          # 实际和弦名，按和声节奏循环，如 ["F#m","D","A","E"]
    chords: dict               # 和弦名 -> 相对根音的半音列表
    vel_scale: float
    style: str
    style_spec: dict           # 已叠加 style_tweaks 的风格参数（只读，不要改）
    density: str | None = None  # 鼓密度档：None / light / medium / full
    crash: bool = False         # 段落起点是否加吊镲
    fill: bool = True           # 是否每 4 小节加过门
    seed: int = 0
    rng: random.Random | None = None   # seed=0 时为 None，输出完全确定
    # 主旋律已经占用的音高（按小节）：铺底声部据此让位，避免同音高同时响
    occupied: dict = field(default_factory=dict)
    lead_playing: bool = False
    # 每个和弦占几拍：4 = 一小节一个，2 = 半小节一个，8 = 两小节一个
    beats_per_chord: float = 4.0
    beats_per_bar: int = 4
    # 0 = 直拍；0.33 大约是"三连音感"，0.66 是很夸张的 shuffle
    swing: float = 0.0
    # 段内密度走向：None=整段一个密度 / "up"=渐强 / "down"=渐弱（见 density_at）
    build: str | None = None
    # 主旋律实际写下的音符 (start, end, pitch)，供副旋律/铺底避让
    lead_notes: list = field(default_factory=list)
    # 副旋律在哪一侧："low" 压在主旋律下面 / "high" 抬到上面 / None = 用风格里的设置
    counter_voice: str | None = None
    # 底鼓落在哪些拍位：{小节(段内): {拍偏移}}，供 bass 咬合（drums 必须先于 bass 构建）
    kick_steps: dict = field(default_factory=dict)

    # ---------- 时间 ----------

    @property
    def beat(self) -> float:
        return 60.0 / self.bpm

    @property
    def bar_len(self) -> float:
        return self.beats_per_bar * self.beat

    def bar_time(self, index: int) -> float:
        """第 index 小节（相对本段起点）的绝对开始时间。"""
        return (self.start_bar + index) * self.bar_len

    def swing_shift(self, beat_offset: float) -> float:
        """8 分音符摇摆：把每拍的后半拍往后推。

        完整 swing 会把后半拍推到 2/3 拍位置，位移量是 beat/6；
        这里按 swing 系数缩放，所以 1.0 是"三连音感觉"，0.5 是轻微 shuffle。
        """
        if not self.swing:
            return 0.0
        frac = beat_offset % 1.0
        if abs(frac - 0.5) < 1e-6:
            return self.swing * self.beat / 6.0
        return 0.0

    def at(self, bar_index: int, beat_offset: float = 0.0) -> float:
        """小节 + 拍偏移 -> 绝对秒数（已含 swing）。

        所有 pattern 都该用它定位，不要自己写 `bar_time + offset * beat`，
        否则 swing 会漏掉某些轨 —— 那比没有 swing 更难受。
        """
        return self.bar_time(bar_index) + beat_offset * self.beat \
            + self.swing_shift(beat_offset)

    # ---------- 和声 ----------

    def chord_index(self, bar_index: int, beat_offset: float = 0.0) -> int:
        """把（小节 + 拍偏移）换算成进行的下标，实现半小节换和弦。"""
        beats = bar_index * self.beats_per_bar + beat_offset
        return int((beats + 1e-9) // self.beats_per_chord)

    def chord_at_beat(self, bar_index: int, beat_offset: float) -> str:
        """某一拍位上正在响的和弦。半小节换和弦时，同一小节会得到两个不同答案。"""
        return self.progression[self.chord_index(bar_index, beat_offset) % len(self.progression)]

    def chord_spans(self, bar_index: int):
        """把一小节切成和声段：[(起始拍, 时长拍, 和弦名), ...]。

        beats_per_chord=4 时只有一个段（一小节一个和弦）；
        =2 时是两段（半小节换和弦）；=8 时每两小节才换一次。
        """
        spans = []
        cursor = 0.0
        while cursor < self.beats_per_bar - 1e-9:
            index = self.chord_index(bar_index, cursor)
            boundary = (index + 1) * self.beats_per_chord - bar_index * self.beats_per_bar
            end = min(float(self.beats_per_bar), boundary)
            if end <= cursor + 1e-9:
                end = float(self.beats_per_bar)
            spans.append((cursor, end - cursor, self.progression[index % len(self.progression)]))
            cursor = end
        return spans

    def chord_end_beat(self, bar_index: int, beat_offset: float) -> float:
        """当前和弦在本小节内结束于第几拍（用于把音符时长切在换和弦处）。"""
        for start, span, _ in self.chord_spans(bar_index):
            if start - 1e-9 <= beat_offset < start + span - 1e-9:
                return start + span
        return float(self.beats_per_bar)

    # ---------- 随机演奏 ----------

    def jitter(self, velocity: int, spread: int = None) -> int:
        """力度微扰动。seed=0 时原样返回，保证同参数可复现。

        spread 不给就用风格的 humanize.velocity（默认 4）。
        """
        if self.rng is None:
            return max(1, min(127, int(velocity)))
        if spread is None:
            spread = int(self.humanize.get("velocity", 4))
        return max(1, min(127, int(velocity) + self.rng.randint(-spread, spread)))

    def sway(self, seconds: float, amount: float = None) -> float:
        """时值微摆动。amount 不给就用风格的 humanize.sway（默认 ±8ms）。

        量很小，只为让不同 take 听起来像不同次演奏。
        """
        if self.rng is None:
            return seconds
        if amount is None:
            amount = float(self.humanize.get("sway", 0.008))
        return max(0.0, seconds + self.rng.uniform(-amount, amount))

    @property
    def humanize(self) -> dict:
        """风格里的 humanize 参数（力度扰动幅度、时值摆动秒数）。"""
        return self.style_spec.get("humanize") or {}

    def chance(self, probability: float) -> bool:
        """按概率决定是否加装饰音。seed=0 时永远为 False。"""
        return self.rng is not None and self.rng.random() < probability

    def pick(self, options):
        """从多个变体里挑一个。seed=0 时固定取第一个。"""
        if self.rng is None:
            return options[0]
        return options[self.rng.randrange(len(options))]

    # ---------- 声部避让 ----------

    def occupy(self, bar_index: int, pitches) -> None:
        """登记这一段已被主旋律占用的音高。

        `bar_index` 是**段落内**的小节号，但 `occupied` 是全曲共享的字典
        （compose 只建一次），所以这里要换算成绝对小节号再存 ——
        否则主歌第 3 小节占的音高会误伤副歌第 3 小节，pad/arp 会莫名少音。
        """
        self.occupied.setdefault(self.start_bar + bar_index, set()).update(pitches)

    def is_occupied(self, bar_index: int, pitch: int) -> bool:
        return pitch in self.occupied.get(self.start_bar + bar_index, ())

    def register_lead(self, start: float, end: float, pitch: int) -> None:
        """登记主旋律的一个音，供副旋律判断"这里有没有空"。"""
        self.lead_notes.append((start, end, pitch))

    # ---------- 段落内动态 ----------

    def density_at(self, bar_index: int):
        """这一小节该用哪一档鼓密度。段落内渐强/渐弱在这里插值。

        一整段只有一个密度，听起来就是"平的"；`arrange.<段>.build` 让密度在段内
        从低一档爬到本段密度（up），或者反过来（down）。默认 None = 整段不变。

        bar_index 是段内小节号。不用 ctx.bars 做分母的话，8 小节和 2 小节的段落
        会得到完全不同的坡度，所以这里按"段内进度"插值。
        """
        if not self.build or not self.density:
            return self.density

        # 延迟导入：context 被所有 pattern 依赖，别在 import 期把 arrange 拉进来
        from core.arrange import DRUM_LADDER

        if self.density not in DRUM_LADDER:
            return self.density

        target = DRUM_LADDER.index(self.density)
        neighbor = max(0, target - 1)
        start, end = (neighbor, target) if self.build == "up" else (target, neighbor)

        span = max(1, self.bars - 1)
        progress = min(1.0, max(0.0, bar_index / span))
        index = round(start + (end - start) * progress)
        return DRUM_LADDER[max(0, min(len(DRUM_LADDER) - 1, index))]

    # ---------- 节奏咬合 ----------
    def register_kick(self, bar_index: int, beat_offset: float) -> None:
        """登记底鼓落点。bass 用它跟自己对齐 —— 所以 drums 必须先于 bass 构建。

        存拍位而不是秒数：bass 的节奏型也是拍位，直接在同一个坐标系里比，不用算 swing。
        """
        self.kick_steps.setdefault(bar_index, set()).add(round(float(beat_offset), 3))

    def kicks_in(self, bar_index: int):
        """某一小节里底鼓的拍位（升序）。"""
        return sorted(self.kick_steps.get(bar_index, ()))

    def lead_sounding(self, start: float, end: float) -> bool:
        """主旋律在 [start, end) 内是否正在响。"""
        return any(s < end - 1e-6 and start < e - 1e-6 for s, e, _ in self.lead_notes)
