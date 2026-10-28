# AI MIDI Arranger

大模型用 Python 生成多轨 MIDI → Logic Pro 预览与重制的工程化编曲工坊。

不依赖 Suno / Udio 等在线整曲生成服务。所有创作决策留在代码里，可版本化、可回滚、可复用。

## 目录结构
```
music_arrangement/
├── agents.md                  # WorkBuddy 全局规则
├── USER.md                    # 个人偏好与审美设定
├── README.md
├── docs/                      # code review 等文档
├── music/                     # 代码包
│   ├── core/
│   │   ├── compose.py         # 主入口：编排调度 + 写出 + 触发体检
│   │   ├── arrange.py         # 段落编排矩阵（哪段哪些轨出声/鼓密度/力度）
│   │   ├── config.py          # 默认参数 + 项目 config.json 加载与校验
│   │   ├── theory.py          # 乐理与 GM 映射（和弦数据的唯一来源）
│   │   └── report.py          # 产物体检
│   └── patterns/              # 各音轨生成逻辑
│       ├── chords.py
│       ├── bass.py
│       ├── drums.py
│       ├── lead.py
│       └── pad.py
├── projects/                  # 每个项目独立目录
│   └── demo/
│       ├── config.json        # 本项目唯一参数源（BPM/调性/段落）
│       └── music/output/      # MIDI 与参数快照
├── tools/
│   ├── init_env.sh
│   ├── compose.sh
│   └── check.sh
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
```
## 日常使用
```
bash tools/compose.sh projects/demo            # 版本号自动递增，不覆盖旧版
bash tools/compose.sh projects/demo v5          # 指定版本号
bash tools/check.sh projects/demo/music/output/demo-v5.mid projects/demo
```

生成后会自动跑一遍体检，输出每轨音符数/音域/力度/结束位置，以及段落是否空白。
体检不通过会以非零退出码返回。

## Logic Pro 导入

拖 `.mid` 到 Tracks 区，5 轨自动分离（PPQ 960，BPM 读文件）：
```
chords → Alchemy Pad / Piano
bass → Studio Bass
drums → Drum Machine Designer（GM 映射，channel 10）
lead → Alchemy Lead / ES2
pad → Sculpture / Strings
```

## 改曲子 = 改代码

| 想改什么 | 改哪个文件 |
|---------|-----------|
| 这首歌的 BPM/调性/结构 | `projects/<dir>/config.json` |
| 段落编排（哪段进鼓、进旋律） | `music/core/arrange.py` |
| 和弦进行 / 和弦构成 | `music/core/theory.py` |
| 和弦织体 | `music/patterns/chords.py` |
| 贝斯律动 | `music/patterns/bass.py` |
| 鼓密度与过门 | `music/patterns/drums.py` |
| 旋律动机 | `music/patterns/lead.py` |
| 铺底声部 | `music/patterns/pad.py` |

改完重跑 `compose.sh`，版本号自动 +1，旧版原样保留。

**注意**：`music/core/config.py` 里的是**默认值**，只有项目没有 `config.json` 时才生效。
想让某一首歌改参数，改那份 `config.json`，不要动默认值。

## 新增一首歌
```
mkdir -p projects/20251028-dark-pop-001/music/output
cp projects/demo/config.json projects/20251028-dark-pop-001/
# 改这份 config.json 的 bpm / key / sections
bash tools/compose.sh projects/20251028-dark-pop-001
```

## 段落与编排

`config.json` 的 `sections` 顺序就是时间轴顺序，键名必须在 `arrange.py` 的 `ARRANGE` 里存在，
否则直接报错（不会像旧版那样静默丢掉整段）。

| 段落 | chords | bass | drums | lead | pad | 力度 |
|------|--------|------|-------|------|-----|------|
| intro | ✓ | — | — | — | ✓ | 0.70 |
| verse | ✓ | ✓ | half | — | ✓ | 0.85 |
| chorus | ✓ | ✓ | full | ✓ | ✓ | 1.00 |
| bridge | ✓ | ✓ | hat | — | ✓ | 0.80 |
| outro | ✓ | — | — | — | ✓ | 0.65 |

## 常见问题

`pretty_midi` 找不到 → `source venv/bin/activate` 后再跑

鼓轨不对 → 确认 GM 映射 kick=36 snare=38 hat=42

报 `未知段落 'xxx'` → 该段落还没在 `music/core/arrange.py` 的 `ARRANGE` 里定义

报 `swing 尚未实现` / `只实现 4/4` → 这两项目前是硬约束，config 里不要写别的值

体检报「段落 xxx 没有任何音符」→ 多半是编排矩阵里该段所有轨都被关掉了
