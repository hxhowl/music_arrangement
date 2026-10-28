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
5. 输出：mid 路径 + 风格/调性/和弦 + 体检结论 + 一条 Logic 导入提示

## 产物约定
- 输出 `projects/<dir>/music/output/<project>-vN.mid`（Format 1，PPQ 960）
- 同时写 `<project>-vN.config.json` 参数快照，保证这一版永久可复现
- 版本号缺省自增，不覆盖旧版；要指定就 `bash tools/compose.sh <dir> v5`

## 代码规则
- **三层分工**：`music/core/arrange.py` 决定哪段出声 / 鼓多密（none/light/medium/full）/ 多响；
  `music/core/styles.py` 决定这一档具体怎么打；`config.json` 决定 bpm / key / progression / style
- pattern 签名统一 `build(inst, ctx)`，`ctx` 是 `music/core/context.py` 的 `Ctx`；
  禁止 `if section == ...`，禁止写死音高或节奏常量
- 旋律按**和弦音级**取音（`music/patterns/lead.py` 的 `_chord_tones`），不要写死半音数
- 和弦由 `theory.build_progression(key, 级数)` 推导，不要写绝对和弦名
- MIDI：Format 1 / PPQ 960 / 鼓 `is_drum=True` 落 channel 10 /
  没有音符的轨不写进文件（避免 Logic 出现空白轨）

## 加一套新风格

`music/core/styles.py` 里加一条，键名就是 `config.json` 能写的 `style` 值：

```python
"pop_dark": dict(
    chords=dict(octave=3, hold=0.8, velocity=56),      # octave/hold(占小节比例)/velocity
    bass=dict(octave=1, low=33, high=44, velocity=86,
              rhythm=[(0.0, 0.45, 1.0, 0), (2.0, 0.45, 0.9, 0)]),  # (起始拍, 时长拍, accent, 半音偏移)
    drums={"light": ..., "medium": ..., "full": ...},   # (GM键名, 起始拍, 时长拍, 基准力度)
    lead=dict(target=69, breath_every=4,
              phrases=[[(0, 0.0, 0.8), (1, 1.0, 0.8)]]),  # (和弦内第几个音, 起始拍, 时长拍)
    pad=dict(octave=3, intervals=(12, 16, 19), velocity=34, hold=0.98),
),
```

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
| `patterns 目前只实现 4/4` | `time_sig` 不是 4/4 |
| `swing 尚未实现` | config 里不要写 `swing` |

## 边界
不自动 bounce 音频；不做人声；长度随意（小样就用 `--duration 20` 或短 `sections`，
正式出一整首）。
