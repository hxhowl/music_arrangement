# AI MIDI Arranger

大模型用 Python 生成多轨 MIDI → Logic Pro 预览与重制的工程化编曲工坊。

不依赖 Suno / Udio 等在线整曲生成服务。所有创作决策留在代码里，可版本化、可回滚、可复用。

## 一句话出一首编曲

```bash
bash tools/new_song.sh "60秒 悬疑感 缓慢推进" --duration 60 --key Am
bash tools/compose.sh projects/20261028-cinematic-001
```

`new_song.sh` 会从描述里推断风格与 BPM（可被 `--style` / `--bpm` 覆盖），
建好项目目录、`brief.md`、`config.json`、`decisions.md`，然后一条命令出 MIDI。

## 目录结构
```
music_arrangement/
├── agents.md                  # WorkBuddy 全局规则
├── USER.md                    # 稳定的协作偏好（不含音乐定位 —— 定位由每次输入决定）
├── README.md
├── docs/
│   ├── music_knowledge/       # 音乐创作知识（分轨策略 / 听感定位 / 乐器选择）
│   └── *.md                   # code review / 可行性审核（冻结的历史记录）
├── music/                     # 代码包
│   ├── core/
│   │   ├── compose.py         # 主入口：编排调度 + 写出 + 触发体检
│   │   ├── arrange.py         # 段落编排矩阵（哪段哪些轨出声、鼓多密、多响）
│   │   ├── styles.py          # 风格库：每套风格怎么演奏（律动/织体/音区）
│   │   ├── context.py         # 传给 pattern 的上下文（bpm/和弦/风格/力度）
│   │   ├── config.py          # 默认参数 + 项目 config.json 加载与校验
│   │   ├── theory.py          # 乐理：调性 -> 级数 -> 和弦，GM 映射
│   │   ├── cues.py            # 音效时间点清单（采样类音效不做成 MIDI 轨）
│   │   └── report.py          # 产物体检
│   └── patterns/              # 各音轨生成逻辑（数据驱动，不写死风格）
│       ├── chords.py          # 和弦（带 voice leading）
│       ├── bass.py
│       ├── drums.py
│       ├── perc.py            # 沙锤/铃鼓/侧击
│       ├── arp.py             # 琶音织体
│       ├── lead.py            # 主旋律
│       ├── counter.py         # 副旋律（只在主旋律空档出声）
│       └── pad.py
├── projects/                  # 每个项目独立目录
│   └── demo/
│       ├── brief.md
│       ├── config.json        # 本项目唯一参数源
│       ├── decisions.md
│       └── music/output/      # MIDI 与参数快照
├── tests/                     # pytest（理论/配置/风格/编排/渲染）
├── tools/
│   ├── init_env.sh
│   ├── new_song.sh            # 从一句话建项目
│   ├── compose.sh
│   ├── instruments.sh         # 列出可选乐器与编制预设
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
bash tools/new_song.sh "90秒 欢快片头 结尾反差" --duration 90 --key C
bash tools/compose.sh projects/20261028-playful-001        # 版本号自动递增
bash tools/compose.sh projects/demo v5                      # 指定版本号
bash tools/check.sh projects/demo/music/output/demo-v5.mid projects/demo
bash tools/instruments.sh                                 # 看每个槽可选哪些乐器
```

生成后会自动体检，输出每轨音符数/音域/力度/结束位置、风格与和弦、段落是否空白。
不通过会以非零退出码返回。同时写两份副产物：

- `<name>-vN.config.json` — 参数快照，保证这一版永久可复现
- `<name>-vN.cues.md` — **音效时间点**（第几小节放 riser / impact），交给你在 Logic 里摆

## 先读一下知识库

如果要调整音乐本身（而不是命令行参数），先看 `docs/music_knowledge/`：

- [分轨策略](docs/music_knowledge/01-分轨策略.md) —— 为什么按功能分 8 层，想加乐器轨之前必读
- [听感问题定位](docs/music_knowledge/02-听感问题定位.md) —— "糊 / 吵 / 空 / 平"分别是哪一层的问题
- [乐器选择](docs/music_knowledge/03-乐器选择.md) —— 每个功能槽用什么乐器，有哪些坑

## 一份编曲由三样东西决定

| 层 | 出厂默认在哪 | 这一首怎么改 | 决定什么 |
|---|---|---|---|
| **段落编排** | `music/core/arrange.py` 的 `ARRANGE` | `config.json` 的 `arrange` | 哪段有哪些轨、鼓多密（none/light/medium/full）、力度、吊镲与过门、**这一段用哪套风格** |
| **风格** | `music/core/styles.py` 的 `STYLES` | `config.json` 的 `style`（整首）+ `style_tweaks`（微调） | 同一档"medium"在 cinematic 是心跳鼓、在 pop 是标准 4/4 |
| **调性与进行** | — | `config.json` 的 `key` + `progression` | 实际和弦，如 `Am` + `i-VI-III-VII` → Am-F-C-G |

三者正交：换风格不影响段落结构，换调不影响律动。

**改动只作用于当前这首歌**：前两层是出厂默认库，项目靠 `arrange` / `style_tweaks`
覆盖，不需要（也不应该）改 `music/core/` 下的文件。

## config.json 字段

| 字段 | 作用 |
|---|---|
| `bpm` / `key` / `progression` | 速度、调性、和弦进行（级数） |
| `style` | 整首歌的主基调，四选一：cinematic / pop / lofi / playful |
| `sections` | 段落顺序与长度 |
| `style_tweaks` | **只对这一首**微调风格参数，如 `{"bass": {"velocity": 78}}` |
| `arrange` | **只对这一首**覆盖段落：`drums` / `vel` / `crash` / `fill` / `style` |
| `seed` | `0` = 完全确定；`>0` = 随机演奏（力度/时值/装饰音/短语起点） |
| `harmonic_rhythm` | **每个和弦占几拍**：`4`=一小节一个，`2`=半小节一个，`8`=两小节一个。不写则用风格默认值 |
| `swing` | 8 分音符摇摆 `0~0.8`：0=直拍，0.33≈三连音感，0.66≈shuffle |
| `preset` | 编制预设：`band` / `cinematic` / `lofi` / `acoustic` / `electronic` |
| `instruments` | 按槽换乐器，如 `{"chords": "nylon", "lead": "flute"}` |
| `cues` | 手动补充的音效时间点，如 `[{"bar": 21, "beat": 3, "what": "whoosh"}]` |
| `velocity_base` | 整体力度，80 为基准 |

## 八条轨的分工

| 轨 | 作用 | 设计要点 |
|---|---|---|
| `chords` | 和声节奏层 | 按 **voice leading** 排列：每个声部走最近的八度；跟随和声节奏分块 |
| `bass` | 低音 | 统一折进一个八度窗口；根音取自**该拍位**的和弦，音尾切在换和弦处 |
| `drums` | 鼓组 | 分档密度 + 过门 + 吊镲 |
| `perc` | 装饰打击乐 | 沙锤/铃鼓/侧击，撑"律动感"但不占低频 |
| `arp` | 琶音织体 | 和弦音上下行分解，填中高频空隙 |
| `lead` | 主旋律 | 按和弦音级取音，**音区独占** |
| `counter` | 副旋律 | 只在**主旋律空档**出声，音区压在 lead 之下，像"回话" |
| `pad` | 铺底 | 有旋律时自动压低（`duck`），并让开 lead / counter 占用的音高 |

`counter` 是"机会性"声部：编排开了它，但它只在主旋律不响的地方写音。
所以副歌旋律铺满时它可能一个音都不出 —— 这是设计，不是故障，体检不会因此报警。

**关于音区重叠**：所有轨的音域天然重叠，这是正常的（真实乐器也这样）。
体检不检查"音区是否重叠"，只检查**同一时刻响同一个音高**——那会让旋律失去轮廓。
`pad` 和 `arp` 会主动避开 `lead` 正在响的音高，所以这项检查现在是 0。

## 测试

```bash
pip install -r requirements.txt pytest
pytest
```

111 项，约 1 秒跑完。覆盖：乐理推导、配置校验、风格/编排合并（含全局不被污染）、
生成确定性与多 take、段落换风格只影响该段、旋律无同音冲突、
**半小节换和弦 / 两小节一个和弦 / swing 只推后半拍 / 副旋律不与主旋律重叠 / 音效清单 /
乐器预设与覆盖优先级 / 换乐器时弹法跟着变 / 鼓组不被 perc 覆盖 / 文档不出现重复行**。

另有 `tests/test_docs.py` 专门查文档本身（`decisions.md` 的版本标题唯一且递增、
文档里没有整块重复、反引号里的仓库路径真实存在、相对链接不失效、
skill 的 `name` 与目录名一致）。
这类错误不影响运行，但会让后来的人（和 AI）照着错的做——所以也纳进 pytest。

## 四种风格

| 风格 | 和声节奏 | 和弦 | 贝斯 | 鼓 | 旋律 |
|---|---|---|---|---|---|
| `cinematic` | 8 拍（两小节一个） | 长音铺满 | 全音符 | 心跳底鼓 | 两音大跳、长音 |
| `pop` | 4 拍（一小节一个） | 0.88 小节 | 八分推进 + 五度 | 标准 4/4 | 四音级进 |
| `lofi` | 2 拍（半小节一个） | 0.72 小节、七和弦 | 切分 + 休止 | 半拍、弱踩镲 | 短句切分 |
| `playful` | 4 拍（一小节一个） | 0.35 小节（断奏） | 切分 + 八度跳 | 错位重音 | 高音区跳进 |

## 段落与编排

`config.json` 的 `sections` 顺序就是时间轴顺序，键名必须在 `ARRANGE` 里存在，
否则直接报错（不会静默丢掉整段）。

| 段落 | chords | bass | drums | perc | arp | lead | counter | pad | 力度 | 风格 |
|---|---|---|---|---|---|---|---|---|---|---|
| intro | ✓ | — | — | — | ✓ | — | — | ✓ | 0.70 | 跟整首 |
| verse | ✓ | ✓ | medium | ✓ | — | — | ✓ | ✓ | 0.85 | 跟整首 |
| chorus | ✓ | ✓ | full | ✓ | ✓ | ✓ | — | ✓ | 1.00 | 跟整首 |
| bridge | ✓ | ✓ | light | — | ✓ | — | ✓ | ✓ | 0.80 | 跟整首 |
| outro | ✓ | — | — | — | — | — | — | ✓ | 0.65 | 跟整首 |

`crash` 只有副歌为 `true`；`fill` 除 intro/outro 外为 `true`。
副歌默认不开 `counter` —— 那里要把空间留给主旋律；想开就 `arrange.chorus.counter = true`。

想只改这一首，就在 `config.json` 里写覆盖，不用动上面的表：

```jsonc
"arrange": {
  "chorus": { "drums": "medium", "vel": 1.05 },
  "outro":  { "style": "playful" }
},
"style_tweaks": { "bass": { "velocity": 78 }, "lead": { "breath_every": 8 } }
```

## 段落换风格（主基调 + 局部反差）

`style` 定整首的主基调，`arrange.<段>.style` 让某一段换风格 —— 这是"电影感但结尾反差"
这类描述的落地方式：

```jsonc
{
  "style": "cinematic",                     // 整首电影感
  "arrange": {
    "chorus": { "style": "pop" },           // 副歌推起来
    "outro":  { "style": "playful" }        // 结尾突然无厘头
  }
}
```

实测（主歌不动、副歌换 playful）：副歌和弦从 2.38 秒长音变成 0.84 秒断奏，
贝斯 4 → 16 个音，鼓 20 → 53 个音，主歌一个音符都没变。

注意：`style_tweaks` 对**所有段落**生效（包括换了风格的段落），因为它改的是
"这首歌的演奏参数"，不是"某个风格的定义"。

## 和声节奏（半小节换和弦）

`harmonic_rhythm` = 每个和弦占几拍。默认跟风格走（cinematic 8 / pop 4 / lofi 2 / playful 4），
写进 config 就覆盖整首：

```jsonc
"harmonic_rhythm": 2      // 半小节换一次：一小节走两个和弦
```

实测（Am，`i-VI-III-VII`，120bpm，`harmonic_rhythm=2`）：

```
bar1 第 0 拍  E3 A3 C4   (Am)      贝斯 A1
bar1 第 2 拍  F3 A3 C4   (F)       贝斯 F2
bar2 第 0 拍  E3 G3 C4   (C)       贝斯 C2
bar2 第 2 拍  D3 G3 B3   (G)       贝斯 G2
```

所有轨都跟着走：`bass` 的根音取自**该拍位**的和弦，音尾切在换和弦处；
`chords` 按块重新分配声部（仍然走 voice leading）；`arp` / `pad` 每块重新起音；
`lead` 每个音用自己所在拍位的和弦，所以换和弦时旋律自动跟着换。

> 注意 `harmonic_rhythm=8` 时和弦是**同一个和弦重复两小节**（每小节仍重新起音一次，
> 这是 comping，不是 bug）。真正的"和声变化"发生在每 8 拍。

## swing（8 分音符摇摆）

```jsonc
"swing": 0.33       // 0=直拍，0.33≈三连音感，0.66≈shuffle
```

实现是把**每拍的后半拍**往后推 `swing × beat / 6`。120bpm、`swing=0.6` 时，
后半拍统一后移 0.05 秒，正拍不动 —— 所有轨都走同一个 `ctx.at()`，所以鼓、贝斯、
琶音、旋律会一起摇，不会出现"鼓摇弦不摇"的错位。

## 音效时间点（cues）

每次生成会顺手写一份 `<name>-vN.cues.md`：

| 时间 | 小节.拍 | 音效 | 为什么在这里 |
|---|---|---|---|
| 0:06 | 3.1 | riser（铺 2 小节渐强） | 给陈述段做 build-up |
| 0:11 | 5.1 | impact + sub drop | 陈述段进入，鼓第一次进来 |
| 0:34 | 13.1 | impact（轻） | 高潮段进入 |

**为什么不直接做成第 9 条轨**：riser / impact / whoosh 是**采样**，MIDI 只能触发
合成器音色 —— 塞进 MIDI 得到的是"一段莫名其妙的合成器声"。所以这条链路给的是
**时间点**，你在 Logic 建一条 `SFX` 音频轨，把采样摆上去就行。

规则按段落编排推（段落进入 → impact；鼓第一次进来 → impact + sub drop；
鼓撤掉 → 反向镲；收尾 → downlifter）。想手加点位就写 config 的 `cues`。

## Logic Pro 导入

拖 `.mid` 到 Tracks 区，8 轨自动分离（PPQ 960，BPM 读文件）：
```
chords  → Alchemy Pad / Piano
bass    → Studio Bass
drums   → Drum Machine Designer（GM 映射，channel 10）
perc    → 打击乐采样（沙锤/铃鼓/侧击）
arp     → 拨弦/合成琶音（Pluck / Alchemy）
lead    → Alchemy Lead / ES2
counter → 大提琴 / 圆号 / 低音木管（要比 lead 暗）
pad     → Sculpture / Strings
```

音效不要建 MIDI 轨：新建一条**音频轨** `SFX`，按 `<name>-vN.cues.md` 的小节位置摆采样。

## 改曲子 = 改 config

| 想改什么 | 改哪里 |
|---------|--------|
| 速度 / 段落结构 / 调性 / 和弦进行 | `projects/<dir>/config.json` |
| 换风格 | 同上，改 `style` |
| 只调一两轨的轻重、鼓的疏密、旋律的呼吸 | 同上，`style_tweaks` / `arrange` |
| 和弦换得勤一点 / 慢一点 | 同上，`harmonic_rhythm`（2=半小节，8=两小节） |
| 想要"摇"一点的律动 | 同上，`swing: 0.33` |
| 某个位置要个 riser / whoosh | 同上，`cues` |
| 想多几版挑一个 | 同上，改 `seed`，或 `compose.sh --takes 3` |
| 加一套新风格（全局能力） | `music/core/styles.py` |
| 加一个新段落类型（全局能力） | `music/core/arrange.py` |

改完重跑 `compose.sh`，版本号自动 +1，旧版原样保留。

**注意**：`music/core/` 下的是出厂默认，不是某一首歌的参数。项目里所有个性化都在
`config.json`，所以改一首不会影响别的歌。

## 多版本

```bash
bash tools/compose.sh projects/demo v5 --takes 3   # 出 v5/v6/v7，seed 1/2/3（config seed=0 时）
bash tools/compose.sh projects/demo --seed 9       # 换一个 seed 再出一版
```

seed 只改"演奏细节"——力度扰动、±8ms 时值摆动、鼓的装饰音、旋律从第几句开始，**不改和弦、段落、风格**。
所以拿到的是同一首编曲的几种演奏，适合挑一版再进 Logic 精修。

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

报 `config.arrange['x'] 里有未知字段` / `style_tweaks['x'] 里有未知字段`
→ 字段名拼错了，报错信息里会列出可用字段

报 `只实现 4/4` → 拍号是硬约束（风格里的鼓/贝斯/琶音拍位全按 4 拍写死的）。
  支持 3/4 需要给每套风格重写拍位，不是加个参数的事，目前没做

报 `harmonic_rhythm=… 不合理` → 每和弦 0.5~16 拍，常用 2 / 4 / 8

报 `swing=… 超出范围` → 0~0.8；超过 0.8 基本听不出拍子了

体检报「段落 xxx 没有任何音符」→ 多半是编排矩阵里该段所有轨都被关掉了

调性写 `Bb` 之类降号没问题；和弦名会按调号正确拼写（D 小调的 VI 级是 `Bb` 不是 `A#`）
