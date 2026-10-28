# agents.md

## 项目定位
AI 代码编曲工坊：大模型用 Python 生成多轨 MIDI → Logic Pro 预览与重制。
不依赖 Suno / Udio 等在线整曲生成。

## 环境
- OS: macOS
- DAW: Logic Pro（默认 48k/24bit，导入 MIDI 时读文件 BPM）
- Python: 项目内 venv，依赖见 requirements.txt
- 根目录: ~/Documents/workspace/workbuddy/music_arrangement

## 标准流程（用户只给一句描述时照这个走）

1. **建项目**：`bash tools/new_song.sh "<描述>" [--duration 90] [--key Am] [--style lofi]`
   → 生成 `projects/<date>-<style>-<seq>/`，含 `brief.md` / `config.json` / `decisions.md`
2. **确认参数**：把 `brief.md` 里的风格、调性、和弦、段落读给用户确认
3. **出 MIDI**：`bash tools/compose.sh projects/<dir>`（版本号自动递增，自动体检）
4. **体检不通过就修**，不许当成完成
5. **交付**：mid 路径 + `[风格/调性/和弦]` + Logic 导入说明
6. **收反馈**：用户听完说"鼓太弱"这类 → 按下面的表改代码 → 写进 `decisions.md`

## 硬规则
1. **创作隔离 = 目录 + 参数双隔离**：每个项目在 `projects/<date>-<style>-<seq>/` 独立目录，
   且必须有**自己的 `config.json`**（bpm / key / progression / style / sections）。
   不要为了做新歌去改 `music/core/config.py` 的默认值，也不要改 `styles.py` 里已有风格的参数
   —— 那会让所有历史版本再也生成不出来。
2. 模型只写代码：不手动改 MIDI 二进制；改曲子 = 改代码/配置后重新生成。
3. 不覆盖历史：`tools/compose.sh` 默认版本号自增；每版自动写 `<name>-vN.config.json`
   参数快照，保证任何一版都能原地复现。`decisions.md` 记录每次改动的听感预期。
4. MIDI 规范：
   - 输出 Format 1（多轨分离），PPQ 960（与 Logic 默认对齐）
   - 鼓轨走 GM 映射，channel 10（0-index 9）
   - 音轨名：chords / bass / drums / lead / pad（`arp` 尚未实现，不要凭空引用）
   - 没有音符的轨不写进文件，避免 Logic 里出现空白轨
5. **三层职责不许混**：
   - `music/core/arrange.py`：哪一段出声、鼓多密、多响（**只管结构**）
   - `music/core/styles.py`：同一档密度具体怎么演奏（**只管律动与织体**）
   - `projects/<dir>/config.json`：速度、调性、和弦进行（**只管这首歌的参数**）
   pattern 里禁止写 `if section == ...`，也禁止写死音高/节奏常量。
6. **和弦只有一个来源**：`theory.py` 的 `build_progression(key, 级数)`。
   调性写 `key`，进行写级数（`["i","VI","III","VII"]`），不要写绝对和弦名，
   否则换调就废了。pattern 层禁止自定义和弦表。
7. Logic 只做演奏层：换音色、力度、groove、自动化、人声重录。
8. 上下文最小化：新窗口只加载 agents.md + 当前项目 brief.md/config.json，不继承历史聊天。

## 常用命令
```
bash tools/init_env.sh                                   # 初始化环境
bash tools/new_song.sh "<描述>" --duration 90 --key Am    # 新建项目
bash tools/compose.sh projects/<dir>                      # 生成（版本号自增 + 体检）
bash tools/compose.sh projects/<dir> v3                   # 指定版本
bash tools/check.sh projects/<dir>/music/output/<f>.mid   # 单独体检
```
试听：把 `.mid` 拖进 Logic Pro（本项目不做离线合成）。

## 用户反馈该改哪一层

| 用户说 | 改哪里 |
|--------|--------|
| 太快/太慢/换个调/换和弦进行 | 项目 `config.json` |
| 想要另一种感觉（"太摇滚了""想更空"） | `config.json` 换 `style` |
| 副歌没起来 / 前奏太满 | `music/core/arrange.py` |
| 鼓太弱 / 太吵 / 想要过门 | `music/core/styles.py` 对应风格的 `drums` |
| 贝斯过密 / 走向奇怪 | `music/core/styles.py` 对应风格的 `bass` |
| 旋律没记忆点 | `music/core/styles.py` 对应风格的 `lead` |

改风格库 = 改所有同风格项目。只想改这一首，就复制一份新风格出来再切换。

## 输出约定
每次动作后输出：
- 用了哪个 skill（或说明按 agents.md 流程执行）
- 生成/修改文件清单
- 风格 / 调性 / 和弦 / 版本号
- 产物体检结论（不通过必须说明原因）
- 下一步不超过 3 个可选项
