# USER.md

## 音乐定位：由每次输入决定

这个仓库**不预设音乐定位**。每一首的定位来自当次输入：

- 用户那句描述（情绪、场景、参考画面）
- `new_song.sh` 的参数（`--style` / `--key` / `--bpm` / `--duration` / `--progression`）
- 结果落在该项目的 `brief.md` 与 `config.json`，**只作用于那一首**

所以这里不写「这个项目是做 XX 风格的」——那会把下一首也带偏。

## 默认倾向（仅当输入没说清时参考，可被覆盖）

- 偏电影感、留白、副歌有记忆点，不喜欢堆砌
- 这是"用户没指定时的兜底"，不是硬约束；与当次描述冲突时，一律以描述为准
- 拿不准就先问一句，不要套用上一首的设定

## 工作流
- 代码生成 MIDI → Logic Pro 精修 → 成品
- AI 只出可编辑草稿，不接收黑盒音频当成品
- 人声必须真人录制或明确授权替代方案
- 每次创作 = 独立项目目录 + 独立 WorkBuddy 窗口

## Logic Pro 习惯
- 常用音色：Alchemy / Sculpture / Drum Machine Designer
- 偏好：轻量化量化（保留 groove）、副歌加 layer、主歌做留白
- 导出：先 bounce 30s preview 再审，不憋完整曲

## 技术环境
- macOS + Python 3.10 (pyenv) + pretty_midi
- 项目根目录：~/Documents/workspace/workbuddy/music_arrangement
- 生成链路：brief + config.json → patterns/*.py → compose.py → .mid

## 不接受的事
- AI 人声直接商用
- 模型输出覆盖上一版文件
- 手动改 MIDI 二进制（改曲子 = 改代码）
- 跨项目污染上下文
