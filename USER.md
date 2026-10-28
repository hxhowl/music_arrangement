# USER.md

## 音乐定位
- 场景：父子互动 / 亲子短视频配乐
- 风格：电影感 + 无厘头反差
- 审美：高质感、留白、副歌有记忆点、不堆砌

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
- 生成链路：brief → config.py → patterns/*.py → compose.py → .mid

## 不接受的事
- AI 人声直接商用
- 模型输出覆盖上一版文件
- 手动改 MIDI 二进制（改曲子 = 改代码）
- 跨项目污染上下文