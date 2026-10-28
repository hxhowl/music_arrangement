---
name: midi-compose
description: 按项目 config.json 与风格库生成多轨 MIDI 草图，自动带产物体检
---

# midi-compose

## 触发
已有 `projects/<dir>/config.json`，用户说“生成 MIDI / 出编曲草图 / 换个风格再出一版”。

## 规则
- 每轨一个 Instrument，track 名规范：chords / bass / drums / lead / pad（`arp` 尚未实现）
- 鼓用 GM 映射（kick=36, snare=38, hat=42, clap=40, crash=49, tom_high=50）
- 鼓 Instrument(is_drum=True)，落 channel 10（0-index 9）
- 没有音符的轨不写进文件
- **三层分工**：
  - `arrange.py` 决定哪段出声 / 鼓多密（none/light/medium/full）/ 多响
  - `styles.py` 决定这一档具体怎么打、贝斯什么律动、旋律什么形状
  - `config.json` 决定 bpm / key / progression（级数）/ style
- pattern 里禁止 `if section == ...`，禁止写死音高或节奏常量
- 旋律按**和弦音级**取音（见 `lead.py` 的 `_chord_tones`），不要写死半音数
- 输出到项目 music/output/<project>-v<n>.mid（Format 1，PPQ 960）

## 代码约定
- 每首歌参数在 `projects/<dir>/config.json`（不要改 `music/core/config.py` 的默认值）
- 和弦由 `theory.build_progression(key, 级数)` 推导，不要写绝对和弦名
- 上下文通过 `core/context.py` 的 `Ctx` 传给各 pattern
- 主入口 `music/core/compose.py`，体检 `music/core/report.py`

## 执行
1. 读 `projects/<dir>/brief.md` 与 `config.json`
2. 需要新风格 → 在 `styles.py` 加条目；只调参数 → 改 `config.json`
3. `bash tools/compose.sh projects/<dir>`（版本号自增，生成后自动体检）
4. 体检不通过 → 先修，不要当成完成
5. 输出：mid 路径 + 风格/调性/和弦 + 体检结论 + Logic 导入说明

## 边界
不自动 bounce 音频，不覆盖旧版，先出 8~16 小节小样。
