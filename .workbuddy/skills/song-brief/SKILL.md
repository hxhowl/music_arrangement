---
name: song-brief
description: 当用户说“写一首歌/起个编曲/做个 60 秒配乐”时，先建项目与 brief，不急着写代码
---

# song-brief

## 触发
新项目起点，或用户描述模糊情绪/场景时。

## 步骤
1. 向用户确认或补全：情绪、流派、**目标时长**、调性、结构、参考画面
2. 一条命令建项目（同时生成 brief.md / config.json / decisions.md）：
   ```bash
   bash tools/new_song.sh "<用户的原话描述>" --duration 90 --key Am --style cinematic
   ```
   - 不给 `--style` / `--bpm` 时脚本会按关键词推断，并把推断结果打印出来
   - 描述里命中多种风格时它会提示，用 `--style` 覆盖
   - 段落写死成比例（前奏15% / 主歌38% / 副歌35% / 尾奏12%），可用 `--sections "intro:4,verse:8,..."` 精确指定
3. 打开生成的 `brief.md` 复核：风格、调性、和弦、段落、时长是否对得上用户的描述
4. 与用户确认这四项（**风格 / 调性 / 和弦 / 时长**），有偏差就改 `config.json` 重跑第 2 步
5. 不在此阶段生成 MIDI（生成走 midi-compose）

## 字段说明
- `key` 决定和弦实际音高，`progression` 用级数（`i`/`VI`/`III`/`VII`），不要写绝对和弦名
- `style` 只能是 `styles.py` 里已定义的（cinematic / pop / lofi / playful）

## 输出
项目目录路径 + `brief.md` 路径 + 一句话创作意图 + 一句“确认风格/调性/时长就可以出 MIDI”。
