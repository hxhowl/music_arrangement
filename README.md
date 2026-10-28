# AI MIDI Arranger

大模型用 Python 生成多轨 MIDI → Logic Pro 预览与重制的工程化编曲工坊。

不依赖 Suno / Udio 等在线整曲生成服务。所有创作决策留在代码里，可版本化、可回滚、可复用。

## 一句话出一首编曲

```bash
bash tools/new_song.sh "60秒 亲子短视频 电影感 慢" --duration 60 --key Am
bash tools/compose.sh projects/20261028-cinematic-001
```

`new_song.sh` 会从描述里推断风格与 BPM（可被 `--style` / `--bpm` 覆盖），
建好项目目录、`brief.md`、`config.json`、`decisions.md`，然后一条命令出 MIDI。

## 目录结构
```
music_arrangement/
├── agents.md                  # WorkBuddy 全局规则
├── USER.md                    # 个人偏好与审美设定
├── README.md
├── docs/                      # code review / 可行性审核
├── music/                     # 代码包
│   ├── core/
│   │   ├── compose.py         # 主入口：编排调度 + 写出 + 触发体检
│   │   ├── arrange.py         # 段落编排矩阵（哪段哪些轨出声、鼓多密、多响）
│   │   ├── styles.py          # 风格库：每套风格怎么演奏（律动/织体/音区）
│   │   ├── context.py         # 传给 pattern 的上下文（bpm/和弦/风格/力度）
│   │   ├── config.py          # 默认参数 + 项目 config.json 加载与校验
│   │   ├── theory.py          # 乐理：调性 -> 级数 -> 和弦，GM 映射
│   │   └── report.py          # 产物体检
│   └── patterns/              # 各音轨生成逻辑（数据驱动，不写死风格）
│       ├── chords.py
│       ├── bass.py
│       ├── drums.py
│       ├── lead.py
│       └── pad.py
├── projects/                  # 每个项目独立目录
│   └── demo/
│       ├── brief.md
│       ├── config.json        # 本项目唯一参数源
│       ├── decisions.md
│       └── music/output/      # MIDI 与参数快照
├── tools/
│   ├── init_env.sh
│   ├── new_song.sh            # 从一句话建项目
│   ├── compose.sh
│   └── check.sh
└── .workbuddy/
    └── skills/                # song-brief / midi-compose / midi-iterate / logic-import
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
bash tools/new_song.sh "90秒 亲子 电影感 结尾反差" --duration 90
bash tools/compose.sh projects/20261028-playful-001        # 版本号自动递增
bash tools/compose.sh projects/demo v5                      # 指定版本号
bash tools/check.sh projects/demo/music/output/demo-v5.mid projects/demo
```

生成后会自动体检，输出每轨音符数/音域/力度/结束位置、风格与和弦、段落是否空白。
不通过会以非零退出码返回。

## 一份编曲由三样东西决定

| 层 | 在哪 | 决定什么 |
|---|---|---|
| **段落编排** | `music/core/arrange.py` 的 `ARRANGE` | 哪一段有哪些轨、鼓多密（none/light/medium/full）、力度缩放 |
| **风格** | `music/core/styles.py` 的 `STYLES` | 同一档"medium"在 cinematic 是心跳鼓、在 pop 是标准 4/4 |
| **调性与进行** | 项目 `config.json` 的 `key` + `progression` | 实际和弦，如 `Am` + `i-VI-III-VII` → Am-F-C-G |

三者正交：换风格不影响段落结构，换调不影响律动。

## 四种风格

| 风格 | 和弦 | 贝斯 | 鼓 | 旋律 |
|---|---|---|---|---|
| `cinematic` | 长音铺满 | 全音符 | 心跳底鼓 | 两音大跳、长音 |
| `pop` | 0.88 小节 | 八分推进 + 五度 | 标准 4/4 | 四音级进 |
| `lofi` | 0.72 小节（断） | 切分 + 休止 | 半拍、弱踩镲 | 短句切分 |
| `playful` | 0.35 小节（断奏） | 切分 + 八度跳 | 错位重音 | 高音区跳进 |

## 段落与编排

`config.json` 的 `sections` 顺序就是时间轴顺序，键名必须在 `ARRANGE` 里存在，
否则直接报错（不会静默丢掉整段）。

| 段落 | chords | bass | drums | lead | pad | 力度 |
|---|---|---|---|---|---|---|
| intro | ✓ | — | — | — | ✓ | 0.70 |
| verse | ✓ | ✓ | medium | — | ✓ | 0.85 |
| chorus | ✓ | ✓ | full | ✓ | ✓ | 1.00 |
| bridge | ✓ | ✓ | light | — | ✓ | 0.80 |
| outro | ✓ | — | — | — | ✓ | 0.65 |

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
| 速度 / 段落结构 / 调性 / 和弦进行 | `projects/<dir>/config.json` |
| 换风格 | 同上，改 `style` |
| 加一套新风格 | `music/core/styles.py` 加一条 `STYLES` 条目 |
| 段落里哪轨出声、鼓多密 | `music/core/arrange.py` |
| 加一个新段落类型 | 先加 `ARRANGE`，再用 `new_song.sh --sections` |
| 某轨的演奏细节 | `music/patterns/*.py` |

改完重跑 `compose.sh`，版本号自动 +1，旧版原样保留。

**注意**：`music/core/config.py` 里的是**默认值**，只有项目没有 `config.json` 时才生效。
和弦进行与调性现在都在项目 config 里，不再需要改全局代码。

## 新增一首歌
```
bash tools/new_song.sh "一句话描述" --duration 90 --key Am --style lofi
bash tools/compose.sh projects/<新建目录>
```

## 常见问题

`pretty_midi` 找不到 → `source venv/bin/activate` 后再跑

鼓轨不对 → 确认 GM 映射 kick=36 snare=38 hat=42

报 `未知段落 'xxx'` → 该段落还没在 `music/core/arrange.py` 的 `ARRANGE` 里定义

报 `未知风格 'xxx'` → 该风格还没在 `music/core/styles.py` 的 `STYLES` 里定义

报 `只实现 4/4` / `swing 尚未实现` → 这两项目前是硬约束，config 里不要写别的值

体检报「段落 xxx 没有任何音符」→ 多半是编排矩阵里该段所有轨都被关掉了

调性写 `Bb` 之类降号没问题；和弦名会按调号正确拼写（D 小调的 VI 级是 `Bb` 不是 `A#`）
