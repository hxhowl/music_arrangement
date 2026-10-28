---
name: song-brief
description: 当用户说“写一首歌/起个编曲/做个 60 秒配乐”时，先建项目与 brief，不急着生成 MIDI
---

# song-brief

## 触发
新项目起点，或用户描述模糊情绪/场景时。

## 步骤

1. **补齐四个必填信息**（缺的可以直接问，也可以按下方默认值先跑再确认）：
   情绪/场景、**目标时长**、调性、段落结构。
   - 短视频常见时长：15s ≈ 5~6 小节（84bpm）/ 30s ≈ 10~12 / 60s ≈ 18~24 / 90s ≈ 26~32
   - 用户没提时长就按 60s

2. **一条命令建项目**（同时生成 `brief.md` / `config.json` / `decisions.md`）：
   ```bash
   bash tools/new_song.sh "<用户的原话描述>" --duration 60 --key Am --style cinematic
   ```
   - `--style` / `--bpm` 不给就按关键词推断，脚本会打印推断依据（可覆盖）
   - `--key` **不会按情绪推断**，只跟风格走：cinematic/lofi → Dm，pop → C，playful → G
   - `--progression` 不给就按调式给默认进行（小调 i-VI-III-VII / 大调 I-V-vi-IV）
   - `--duration` 按 前奏15% / 主歌38% / 副歌35% / 尾奏12% 反推段落；
     要精确控制就用 `--sections "intro:4,verse:8,chorus:8,outro:4"`
   - 段落名、风格名、调性写错会在**建目录之前**报错，不会留下半个项目

3. **复核 `brief.md`**：风格、调性、和弦、段落、时长是否对得上用户的描述。

4. **参数要改，直接改该项目的 `config.json`**（字段不多，手改最快）。
   ⚠️ 不要"改完重跑 new_song.sh"—— 它遇到同名目录会自动建 `-002`，你会得到两个项目。

5. **不在此阶段生成 MIDI**（生成走 `midi-compose`）。

## 字段说明

| 字段 | 说明 |
|---|---|
| `bpm` | 20~300 |
| `key` | `C` / `Am` / `F#m` / `Bb` 都可以，降号调支持 |
| `progression` | **级数**（`i`/`VI`/`III`/`VII`），不要写绝对和弦名，否则换调就废了 |
| `style` | 只能是 `music/core/styles.py` 里已定义的（cinematic / pop / lofi / playful） |
| `sections` | 键名必须在 `music/core/arrange.py` 的 `ARRANGE` 里存在 |
| `seed` | `0` = 完全确定（默认）；`>0` = 随机演奏 |
| `style_tweaks` | 只对这一首微调风格参数，建项目时留空即可 |
| `arrange` | 只对这一首覆盖段落编排，建项目时留空即可 |
| `velocity_base` | 80 为基准，整体音量比例 |

## 输出

项目目录路径 + `brief.md` 路径 + 一句话创作意图 +
一句“确认风格/调性/时长就可以出 MIDI”。
