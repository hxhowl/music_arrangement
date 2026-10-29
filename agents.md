# agents.md

## 项目定位
AI 代码编曲工坊：大模型用 Python 生成多轨 MIDI → Logic Pro 预览与重制。
不依赖 Suno / Udio 等在线整曲生成。

**这是一条通用产线，不是一个"固定风格的项目"**：每首歌的音乐定位来自当次输入
（用户那句描述 + `new_song.sh` 的参数），落进该项目的 `brief.md` / `config.json`。
`USER.md` 只放稳定的协作偏好，不预设场景与风格 —— 不要拿上一首的设定套下一首。

## 环境
- OS: macOS
- DAW: Logic Pro（默认 48k/24bit，导入 MIDI 时读文件 BPM）
- Python: 项目内 venv，依赖见 requirements.txt
- 根目录: ~/Documents/workspace/workbuddy/music_arrangement

## 硬规则

1. **改动只作用于当前这首歌**：每首歌独立 `projects/<date>-<style>-<seq>/`，
   且必须有自己的 `config.json`。调歌用 config 里的 `bpm` / `key` / `progression` /
   `style` / `sections` / `style_tweaks` / `arrange` / `seed`，
   **不要改 `music/core/` 下的任何文件** —— 那是出厂默认库，改了会影响所有项目，
   历史版本再也生成不出来。只有"扩产线"（加新风格、新段落类型、新和声手法）才动代码，
   且必须说明影响面。
2. **模型只写代码**：不手动改 MIDI 二进制；改曲子 = 改代码/配置后重新生成。
3. **不覆盖历史**：`tools/compose.sh` 默认版本号自增，每版自动写 `<name>-vN.config.json` 快照。
   `decisions.md` 记录每次改动的听感预期。
4. **三层职责不许混**：`music/core/arrange.py` 管"哪段出声、多密、多响"；
   `music/core/styles.py` 管"这一档具体怎么演奏"；`config.json` 管"这首歌"。
   前两层是出厂默认，项目通过 `arrange` / `style_tweaks` 覆盖，不改源文件。
   pattern 里禁止 `if section == ...`，禁止写死音高与节奏常量。
5. **和弦只有一个来源**：`music/core/theory.py` 的 `build_progression(key, 级数)`。
   调性写 `key`、进行写级数，不要写绝对和弦名。
6. **MIDI 规范**：Format 1、PPQ 960、鼓轨 GM 映射落 channel 10、
   音轨名 chords/bass/drums/lead/pad（`arp` 未实现，不要引用）、空轨不写入文件。
7. **体检不通过不算完成**：`tools/compose.sh` 生成后自动体检，失败必须说明原因。
8. **上下文最小化**：新窗口只加载 agents.md + 当前项目 brief.md/config.json，不继承历史聊天。

## 技能索引

详细步骤都在 skill 里，这里只做路由。**先读对应 SKILL.md 再动手，不要凭印象编流程。**

| 用户意图 | 读这个文件 |
|---|---|
| 起新歌、"帮我做一首…"、描述模糊 | `.workbuddy/skills/song-brief/SKILL.md` |
| 出 MIDI、换风格再出一版、生成失败排查 | `.workbuddy/skills/midi-compose/SKILL.md` |
| 听完要改、"鼓太弱""想更空""换个调" | `.workbuddy/skills/midi-iterate/SKILL.md` |
| 导入 Logic、选音色、试听与验收 | `.workbuddy/skills/logic-import/SKILL.md` |

> skill 若没被自动加载（实测可能出现 `Can not find skill`），直接 Read 上表文件照做即可。

## 常用命令

```
bash tools/init_env.sh                                   # 初始化环境
bash tools/new_song.sh "<描述>" --duration 90 --key Am    # 新建项目
bash tools/compose.sh projects/<dir>                      # 生成（版本自增 + 体检）
bash tools/compose.sh projects/<dir> v5 --takes 3         # 一次出 3 个演奏版本
bash tools/compose.sh projects/<dir> --seed 9             # 换一个 seed 再出一版
bash tools/check.sh projects/<dir>/music/output/<f>.mid   # 单独体检
```

## 输出约定

每次动作后输出：
- 读了哪个 skill（或说明按本文件的哪条规则执行）
- 生成/修改的文件清单
- 风格 / 调性 / 和弦 / 版本号
- 体检结论（不通过要说明原因）
- 下一步不超过 3 个可选项
