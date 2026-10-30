---
name: midi-compose
description: 按项目 config.json 与风格库生成多轨 MIDI，自动带产物体检
---

# midi-compose

## 触发
已有 `projects/<dir>/config.json`，用户说“生成 MIDI / 出编曲 / 换个风格再出一版”。

## 执行
1. 读 `projects/<dir>/config.json`（没有就读 `brief.md` 反推；都没有回 `song-brief`）
2. 需要动参数就改 `config.json`，**不要改 `music/core/config.py` 的默认值**
3. `bash tools/compose.sh projects/<dir>`
4. 体检不通过 → 先修，别当成完成
5. 动过 `music/` 下任何文件，跑 `pytest`（154 项，<2 秒）
6. 输出：mid 路径 + 风格/调性/和弦/和声节奏 + 体检结论 + 音效清单路径 + 一条 Logic 导入提示

## 产物约定
- 输出 `projects/<dir>/music/output/<project>-vN.mid`（Format 1，PPQ 960）
- 同时写 `<project>-vN.config.json` 参数快照（含实际 seed），保证这一版永久可复现
- 同时写 `<project>-vN.cues.md` 音效时间点（riser / impact 放第几小节）。
  **不要把这些音效做成 MIDI 轨**：它们是采样，MIDI 只能触发合成器音色
- 版本号缺省自增，不覆盖旧版；要指定就 `bash tools/compose.sh <dir> v5`
- 同时重写 `projects/INDEX.md`（所有作品的风格/调/最新版本），
  并在终端打印 `[diff] 相比 vN-1：…` —— 这行是"这版改了什么"的唯一来源，回话时带上
- 多版本：`bash tools/compose.sh <dir> v5 --takes 3` → v5/v6/v7，
  seed 从 config 的 `seed` 起递增（默认 0 → 1/2/3）
- 换演奏：`bash tools/compose.sh <dir> --seed 9`

## 代码规则
- **三层分工**：`music/core/arrange.py` 决定哪段出声 / 鼓多密（none/light/medium/full）/
  多响 / **这一段用哪套风格**；`music/core/styles.py` 决定这一档具体怎么打；
  `config.json` 决定这首歌的一切参数
- **项目内覆盖**：`config.json` 的 `style_tweaks` / `arrange` 会叠在出厂默认之上
  （`styles.resolve` 与 `arrange.get` 负责合并），所以调歌不需要改全局文件
- **乐器不在 TRACKS 里**：`compose.TRACKS` 只存 `name` / `is_drum`，program 由
  `music/core/instruments.py` 的 `plan(cfg)` 决定（DEFAULT < `preset` < `instruments`）。
  换乐器只用 config，不要往 TRACKS 里加 program
- **风格是按段解析的**：`compose` 用 `arrange.<段>.style or cfg["style"]` 定该段风格，
  再把结果放进 `ctx.style_spec`；pattern 只读 `ctx.style_spec`，**不要自己 resolve**
- pattern 签名统一 `build(inst, ctx)`，`ctx` 是 `music/core/context.py` 的 `Ctx`；
  禁止 `if section == ...`，禁止写死音高或节奏常量
- 风格参数一律从 `ctx.style_spec` 取，**不要在 pattern 里再 `resolve_style`**
- 旋律按**和弦音级**取音（`music/patterns/lead.py` 的 `_chord_tones`），不要写死半音数
- 和弦由 `theory.build_progression(key, 级数)` 推导，不要写绝对和弦名
- MIDI：Format 1 / PPQ 960 / 鼓与打击乐 `is_drum=True` 落 channel 10 /
  没有音符的轨不写进文件（避免 Logic 出现空白轨）
- 轨：chords / bass / drums / perc / arp / lead / counter / pad，共 8 条
- **构建顺序在 compose 里定死**：chords → drums → bass → lead → perc → arp →
  counter → pad。**drums 必须在 bass 之前**（bass 要读底鼓落点来咬合，见
  `ctx.register_kick` / `bass.lock_kick`）；lead 在 counter/arp/pad 之前
  （它们要读旋律的空档与占用音高）；pad 最后写（避让所有声部）。不要调换
- **拍位一律用 `ctx.at(i, 拍)`**，不要写 `bar_time(i) + 拍 * beat` —— 后者不跟 swing
- **同一小节内的和声用 `ctx.chord_spans(i)`**（半小节换和弦），
  单个拍位查和弦用 `ctx.chord_at_beat(i, 拍)`

## 加一套新风格

⚠️ 这是**扩产线**，不是调这首歌。只想调一首请用 `config.json` 的 `style_tweaks`。
加条目不会改变已有项目的输出（老项目各自有快照），只是多一个可选 `style` 值。

`music/core/styles.py` 里加一条，键名就是 `config.json` 能写的 `style` 值。
最稳的做法是**复制一个现有条目再改**，不要从零写：

```bash
grep -A 20 '"pop": dict' music/core/styles.py   # 看一份完整样例
```

改完大致长这样（字段一个都不能少，少一个会 KeyError）：

```python
"pop_dark": dict(
    chords=dict(octave=3, hold=0.8, velocity=56, range=(48, 67), beats=4),
    bass=dict(octave=1, low=33, high=44, velocity=86,
              rhythm=[(0.0, 0.45, 1.0, 0), (2.0, 0.45, 0.9, 7)]),
    drums={
        "light":  [("kick", 0.0, 0.1, 70)],
        "medium": [("kick", 0.0, 0.1, 88), ("snare", 2.0, 0.1, 74)],
        "full":   [("kick", 0.0, 0.1, 105), ("snare", 1.0, 0.1, 90)],
    },
    lead=dict(target=69, range=(60, 83), velocity=84, breath_every=4,
              breath=((0, 0.0, 1.8), (2, 2.0, 1.8)),
              phrases=[[(0, 0.0, 0.8), (1, 1.0, 0.8)]]),
    pad=dict(octave=3, intervals=(12, 16, 19), velocity=34, hold=0.98, duck=0.75),
    fill=FILL_STD, fill_every=4,
    ghost=dict(chance=0.3, velocity=28),
    humanize=dict(velocity=3, sway=0.008),
    perc=dict(gm="shaker", step=0.5, velocity=32, accents=(0, 2)),
    arp=dict(range=(60, 79), step=0.25, velocity=42, octaves=2),
    counter=dict(range=(55, 71), velocity=60,
                 rhythm=[(1.5, 0.45, 3), (3.5, 0.45, 2)]),
),
```

自检：把这段贴进 `STYLES` 后跑 `python -c "from core.styles import resolve; resolve('pop_dark')"`
—— `_check_shapes` 会把缺字段/越界项当场指出来。

字段含义：

| 字段 | 含义 |
|---|---|
| `chords.hold` | 和弦占小节的比例（0.35 断奏 / 0.99 连绵） |
| `chords.range` | 和弦声部进行的工作区间（voice leading 在这个范围内选音） |
| `chords.seventh` | `True` 时用七和弦（注意：换和弦名，如 Am → Am7） |
| `chords.beats` | 每个和弦占几拍（4=一小节一个，2=半小节一个，8=两小节一个） |
| `bass.rhythm` | `(起始拍, 时长拍, accent, 半音偏移)`，偏移 7=五度、12=八度 |
| `drums[档]` | `(GM 键名, 起始拍, 时长拍, 基准力度)` |
| `lead.range` | 旋律音区 `(最低音, 最高音)` |
| `lead.velocity` | 旋律基准力度 |
| `lead.phrases` | `(和弦内第几个音, 起始拍, 时长拍)`，一组短语按 `(i//2)` 轮换 |
| `lead.breath_every` | 每 N 小节换成长音呼吸，0 = 不呼吸 |
| `lead.breath` | 呼吸小节用的长音，格式同 phrases |
| `fill` | 过门音符 `(GM 键名, 起始拍偏移)`，铺满第 4 拍 |
| `fill_every` | 每 N 小节加一次过门 |
| `ghost` | 反拍轻踩镲 `dict(chance=概率, velocity=力度)`，chance=0 表示不加 |
| `humanize` | `dict(velocity=力度扰动, sway=时值摆动秒)`，只在 seed>0 生效；鼓用固定更小的量 |
| `pad.duck` | 有旋律时 pad 压低的比例（0.7 = 压到七成） |
| `perc` | `dict(gm=鼓件, step=间隔拍, velocity=力度, accents=重拍位置)` |
| `arp` | `dict(range=(最低,最高), step=间隔拍, velocity=力度, octaves=跨八度)` |
| `counter` | `dict(range=(最低,最高), velocity=力度, rhythm=[(起始拍, 时长拍, 音级)])` 副旋律 |

- 三个密度档（light/medium/full）都要有，否则跑该密度的段落会报错
  （`none` 不用定义：`ARRANGE` 里写 `drums=None` 时整段不出鼓）
- 加完立刻 `bash tools/compose.sh projects/<dir>` 验证，并用现有风格做对照
- ⚠️ 改已有风格的参数会影响**同风格的所有项目**；只想改一首就新增风格再切换

## 常见报错

| 报错 | 原因 |
|---|---|
| `未知段落 'xxx'` | 段落没在 `music/core/arrange.py` 的 `ARRANGE` 里定义 |
| `未知风格 'xxx'` | 风格没在 `music/core/styles.py` 的 `STYLES` 里定义 |
| `无法解析级数 'x'` | `progression` 用了非罗马数字，或写了绝对和弦名 |
| `风格 'x' 没有定义鼓密度 'y'` | 新风格缺 density 档 |
| `patterns 目前只实现 4/4` | `time_sig` 不是 4/4（拍位是按 4 拍写死的，加 3/4 要重写风格数据） |
| `harmonic_rhythm=… 不合理` | 每和弦 0.5~16 拍，常用 2 / 4 / 8 |
| `swing=… 超出范围` | 0~0.8 |
| `config.cues 每项至少要有 bar` | `cues` 是 `[{"bar": 21, "beat": 3, "what": "whoosh"}]` |
| `未知编制预设 'x'` | `preset` 只能是 band / cinematic / lofi / acoustic / electronic |
| `chords 没有 'sitar' 这个乐器` | 乐器名写错，报错里会列出该槽全部可选值 |
| `counter_voice=… 不合法` | 只能是 `low` / `high`，或不写（表示用风格里的设置） |
| `build=… 不合法` | 只能是 `null` / `"up"`（渐强）/ `"down"`（渐弱） |

## 边界
- 不自动 bounce 音频；不做人声
- 长度随意：小样用 `--duration 20` 或短 `sections`，正式出一整首
- **seed=0 时完全确定**：同参数两次输出字节相同，便于复现和排查
- **seed>0 是"同一编曲的不同演奏"**：只改力度扰动、±8ms 时值摆动、鼓的装饰音、
  旋律短语起点，不改和弦/段落/风格。要真正换一首请换 `style` 或 `progression`
