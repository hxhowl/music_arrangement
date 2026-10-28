---
name: song-brief
description: 当用户说“写一首歌/起个编曲/做个 demo 简报”时，先生成结构化音乐 brief，不急着写代码
---

# song-brief

## 触发
新项目起点，或用户描述模糊情绪/场景时。

## 步骤
1. 向用户确认或补全：情绪、流派、BPM、调性、结构、人声语言、参考画面
2. 在 projects/<date>-<style>-<seq>/brief.md 生成简报
3. 简报字段：
   - title / mood / genre / bpm / key
   - sections: intro/verse/chorus/bridge/outro（每部分小节数）
   - hook 描述
   - 音轨规划：哪些用代码生成，哪些留 Logic 手作
   - 保留 AI 部分 / 必须真人重做部分
4. brief 定稿后，把 bpm / key / sections **落成同目录的 config.json**
   （否则这些参数只能靠人手抄进代码，迟早抄错）：
   ```bash
   cp projects/demo/config.json projects/<dir>/config.json
   # 再按 brief 改 bpm / key / sections
   ```
   `sections` 的键名必须在 `music/core/arrange.py` 的 `ARRANGE` 里存在。
5. 不在此阶段生成 MIDI

## 输出
brief 路径 + config.json 路径 + 一句话创作意图。