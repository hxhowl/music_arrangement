# agents.md

## 项目定位
AI 代码编曲工坊：大模型用 Python 生成多轨 MIDI → Logic Pro 预览与重制。
不依赖 Suno / Udio 等在线整曲生成。

## 环境
- OS: macOS
- DAW: Logic Pro（默认 48k/24bit，导入 MIDI 时读文件 BPM）
- Python: 项目内 venv，依赖见 requirements.txt
- 根目录: ~/Documents/workspace/workbuddy/music_arrangement

## 硬规则
1. **创作隔离 = 目录 + 参数双隔离**：每个项目在 `projects/<date>-<style>-<seq>/` 独立目录，
   且必须有**自己的 `config.json`**（BPM / 调性 / 段落结构）。
   不要为了做新歌去改 `music/core/config.py` 的默认值——那会让旧版本再也生成不出来。
2. 模型只写代码：不手动改 MIDI 二进制；改曲子 = 改 `music/` 下 Python 代码后重新生成。
3. 不覆盖历史：`tools/compose.sh` 默认版本号自增；每版自动写 `<name>-<vN>.config.json`
   参数快照，保证任何一版都能原地复现。`decisions.md` 记录每次改动的听感预期。
4. MIDI 规范：
   - 输出 Format 1（多轨分离），PPQ 960（与 Logic 默认对齐）
   - 鼓轨走 GM 映射，channel 10（0-index 9）
   - 音轨名：chords / bass / drums / lead / pad（`arp` 尚未实现，不要凭空引用）
   - 没有音符的轨不写进文件，避免 Logic 里出现空白轨
5. **段落编排只有一处**：`music/core/arrange.py` 的 `ARRANGE` 决定每段哪些轨出声、
   鼓的密度、力度缩放。config 里出现 ARRANGE 未定义的段落会直接报错（不静默跳过）。
6. **和弦只有一个来源**：`music/core/theory.py` 的 `CHORDS` / `PROGRESSION`。
   pattern 层禁止再定义一份和弦表。
7. Logic 只做演奏层：换音色、力度、groove、自动化、人声重录。
8. 上下文最小化：新窗口只加载 agents.md + 对应 skill + 当前项目 brief.md，不继承历史聊天。

## 常用命令
```
bash tools/init_env.sh                                  # 初始化环境
bash tools/compose.sh projects/<dir>                    # 生成，版本号自动递增，带产物体检
bash tools/compose.sh projects/<dir> v3                  # 指定版本号
bash tools/check.sh projects/<dir>/music/output/<f>.mid  # 单独体检
```
试听：把 `projects/<dir>/music/output/<file>.mid` 拖进 Logic Pro（本项目不做离线合成）。

## 输出约定
每次动作后输出：
- 用了哪个 skill
- 生成/修改文件清单
- 产物体检结论（不通过必须说明原因，不能当成"已完成"）
- 下一步不超过 3 个可选项
