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
1. 创作隔离：每个项目在 projects/<date>-<style>-<seq>/ 独立目录，新歌新 WorkBuddy 窗口
2. 模型只写代码：不手动改 MIDI 二进制；改曲子 = 改 music/ 下 Python 代码后重新生成
3. 不覆盖历史：输出文件带版本号 -v1 -v2，decisions.md 记录每次决策
4. MIDI 规范：
   - 输出 Format 1（多轨分离）
   - 鼓轨走 GM 映射，channel 10（0-index 9）
   - 音轨名：lead / chords / bass / drums / pad / arp
5. Logic 只做演奏层：换音色、力度、groove、自动化、人声重录
6. 上下文最小化：新窗口只加载 agents.md + 对应 skill + 当前项目 brief.md，不继承历史聊天

## 常用命令
- 初始化环境: bash tools/init_env.sh
- 生成 MIDI: bash tools/compose.sh projects/<dir>
- 试听合成（可选）: bash tools/synthesize.sh music/output/<file>.mid

## 输出约定
每次动作后输出：
- 用了哪个 skill
- 生成/修改文件清单
- 下一步不超过 3 个可选项