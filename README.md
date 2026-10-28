# AI MIDI Arranger

大模型用 Python 生成多轨 MIDI → Logic Pro 预览与重制的工程化编曲工坊。

不依赖 Suno / Udio 等在线整曲生成服务。所有创作决策留在代码里，可版本化、可回滚、可复用。

## 目录结构
```
music_arrangement/
├── agents.md                  # WorkBuddy 全局规则
├── USER.md                    # 个人偏好与审美设定
├── README.md
├── music/                     # 代码包
│   ├── core/
│   │   ├── compose.py         # 主入口
│   │   ├── config.py          # 全局参数 BPM/调性/结构
│   │   └── theory.py          # 乐理工具
│   └── patterns/              # 各音轨生成逻辑
│       ├── chords.py
│       ├── bass.py
│       ├── drums.py
│       └── lead.py
├── projects/                  # 每个项目独立目录
│   └── demo/
│       └── music/
│           └── output/        # MIDI 输出到这里
├── tools/
│   ├── init_env.sh
│   └── compose.sh
└── .workbuddy/
    └── skills/
        ├── song-brief/
        ├── midi-compose/
        ├── midi-iterate/
        └── logic-import/
```
## 环境要求
```
- macOS
- Python 3.10+（pyenv）
- Logic Pro 11+
- WorkBuddy
```
## 首次初始化
```
cd ~/Documents/workspace/workbuddy/music_arrangement
bash tools/init_env.sh
bash tools/compose.sh projects/demo
ls projects/demo/music/output/demo-v1.mid
```
## 日常使用
```
bash tools/compose.sh projects/demo
bash tools/compose.sh projects/20251028-dark-pop-001
```
## Logic Pro 导入

拖 `.mid` 到 Tracks 区，5 轨自动分离：
```
chords → Alchemy Pad
bass → Studio Bass
lead → Alchemy Lead
drums → Drum Machine Designer (GM)
pad → Sculpture
```
## 改曲子 = 改代码

| 想改什么 | 改哪个文件 |
|---------|-----------|
| BPM/调性/结构 | music/core/config.py |
| 和弦进行 | music/core/theory.py |
| 和弦织体 | music/patterns/chords.py |
| 贝斯律动 | music/patterns/bass.py |
| 鼓节奏 | music/patterns/drums.py |
| 旋律动机 | music/patterns/lead.py |

改完重跑 compose.sh，版本号 +1。

## 新增一首歌
```
mkdir -p projects/歌曲名/music/output
改 config.py
改 patterns/（按需）
bash tools/compose.sh projects/歌曲名
```
## 常见问题

`pretty_midi` 找不到 → `source venv/bin/activate` 后再跑
鼓轨不对 → 确认 GM 映射 kick=36 snare=38 hat=42