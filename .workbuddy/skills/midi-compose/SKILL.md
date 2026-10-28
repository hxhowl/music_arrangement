---
name: midi-compose
description: 根据 brief.md，用 pretty_midi 写多轨可编辑 MIDI 草图，输出分轨/合并 mid 文件
---

# midi-compose

## 触发
已有 brief.md，用户说“生成 MIDI / 写和弦贝斯鼓 / 出编曲草图”。

## 规则
- 每轨一个 Instrument，track 名规范：lead/chords/bass/drums/pad/arp
- 鼓用 GM 映射（kick=C1/36, snare=D1/38, hat=F#1/42, clap=E1/40）
- 鼓 Instrument(is_drum=True)，channel=9
- 旋律留白 ≥40%，不写满
- 和弦每小节一换，贝斯跟根音+经过音
- 默认量化 1/16，swing 参数可调
- 输出到项目 music/output/<project>-v<n>.mid（Format 1）

## 代码约定
- 全局参数在 music/core/config.py
- 音符/和弦工具在 music/core/theory.py
- 各轨 pattern 在 music/patterns/*.py
- 主入口 music/compose.py（读 brief 或 config）

## 执行
1. 读 brief.md
2. 写/改 music/ 下对应模块
3. 跑 tools/compose.sh
4. 输出文件清单 + Logic 导入说明

## 边界
不自动 bounce 音频，不覆盖旧版，先出 8~16 小节小样。