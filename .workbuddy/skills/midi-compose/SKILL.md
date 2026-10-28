---
name: midi-compose
description: 根据 brief.md 与项目 config.json，用 pretty_midi 写多轨可编辑 MIDI 草图，自动带产物体检
---

# midi-compose

## 触发
已有 brief.md / config.json，用户说“生成 MIDI / 写和弦贝斯鼓 / 出编曲草图”。

## 规则
- 每轨一个 Instrument，track 名规范：chords / bass / drums / lead / pad（`arp` 尚未实现，不要引用）
- 鼓用 GM 映射（kick=36, snare=38, hat=42, clap=40, crash=49, tom_high=50）
- 鼓 Instrument(is_drum=True)，落 channel 10（0-index 9）
- 没有音符的轨不写进文件（避免 Logic 里出现空白轨）
- 段落差异由 `core/arrange.py` 的 `ARRANGE` 决定，不要在 pattern 里写 `if section == ...`
- 旋律按**和弦音级**取音（见 `patterns/lead.py` 的 `_chord_tones`），不要写死半音数，否则会与和弦打架
- 输出到项目 music/output/<project>-v<n>.mid（Format 1，PPQ 960）

## 代码约定
- 每首歌参数在 `projects/<dir>/config.json`（不要改 `music/core/config.py` 的默认值）
- 段落编排在 `music/core/arrange.py`
- 和弦数据唯一来源 `music/core/theory.py`（pattern 层禁止再定义一份）
- 各轨 pattern 在 `music/patterns/*.py`
- 主入口 `music/core/compose.py`
- 产物体检 `music/core/report.py`

## 执行
1. 读 projects/<dir>/brief.md 与 config.json
2. 写/改 music/ 下对应模块
3. 跑 `bash tools/compose.sh projects/<dir>`（版本号自动递增，生成后自动体检）
4. 体检不通过 → 先修，不要当成完成
5. 输出文件清单 + 体检结论 + Logic 导入说明

## 边界
不自动 bounce 音频，不覆盖旧版，先出 8~16 小节小样。
