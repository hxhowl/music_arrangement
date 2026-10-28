# Code Review — AI MIDI Arranger

日期：2026-10-28
范围：`agents.md` / `README.md` / `USER.md` / `music/**` / `tools/**` / `.workbuddy/skills/**` / 产物 `demo-v1.mid`
方式：静态审阅 + 实际运行验证（含 MIDI 产物二进制解析、参数变异测试）

> **修复状态（2026-10-28 22:45 更新）**
> 五个 P0 已修复；随后完成「编排矩阵 + 配置下沉 + 产物体检」三项工程改造，
> 顺带修掉 P1 里的 outro 空白、pad 空轨、段落无动态、lead 不跟和弦、力度常量。
> 见文末「附录二：P0 修复记录」与「附录三：第二轮改造记录」。
> 基线（修复前）保存在 git commit `d2fb29f`，可用 `git show d2fb29f` 对照。
> 仍未处理：和弦转位/voice leading、swing、arp 轨、brief→config 的自动化。


## 一句话结论

**骨架是对的，实现是"能跑出声音"的 demo 级，还没到"工程化"。**

链路（brief → config → patterns → MIDI → Logic）方向正确，Rule of Law（硬规则）写得比大多数人手写项目都好。
但代码里有 **2 个必然踩到的功能性 Bug**、**3 处违反你自己写的硬规则**、以及 **config 里一半参数是装饰性的**。
现在的状态是"跑一次能听"，不是"可控地做出第二首歌"。

评分（10 分制）：

| 维度 | 分 | 说明 |
|---|---|---|
| 架构与分层 | 7 | 目录/职责清晰，skill 分层有想法 |
| 规则一致性 | 4 | 硬规则 1/3/4 与实际代码不符 |
| 代码正确性 | 4 | 数据双份、Hardcode 音高错误、版本号不生效 |
| 音乐可用性 | 4 | 全部小节同一织体，无动态层次，成片必须重写 |
| 可演进性 | 5 | 加一个和弦要改 4 个文件 |

---

## 一、做对的四件事（先肯定，这些别改）

1. **Format 1 + 鼓轨 channel 10** —— 实测通过。`demo-v1.mid` 是 `type 1`，6 个 track，drums 落在 `chans={9}`，符合硬规则 4。这是最容易做错的地方，做对了。
2. **"改曲子 = 改代码"的定位** —— 拒绝黑盒音频，让创作决策可版本化。这个判断是对的，也是这套链路相对 Suno 的唯一价值。
3. **agents.md 的硬规则写得具体** —— 带版本号、不覆盖历史、上下文最小化、Logic 只做演奏层，边界清楚。
4. **确定性输出** —— 当前无随机，同一份代码必出同一份 MIDI。这是可复现的前提（虽然版本机制没跟上）。

---

## 二、P0：必须先修的 5 个问题

### P0-1 和弦数据写了两份，且改错了地方会崩

`music/patterns/chords.py` 自己重新定义了 `CHORDS / PROGRESSION / NOTE_OFFSET`，**没有** `from core.theory import ...`。
而 `bass.py` / `lead.py` 用的是 `core.theory` 的版本。

实测（把 theory 的进行改成 Am-F-C-G，模拟你按 README 改 theory.py）：

```
同一对象? False
改 theory 后 -> chords 用: ['F#m', 'D', 'A', 'E']     ← 没变
改 theory 后 -> bass/lead 用: ['Am', 'F', 'C', 'G']   ← 变了
bass 报错 -> KeyError 'Am'                            ← 直接崩
```

三重后果：

- 按 README「和弦进行 → 改 music/core/theory.py」操作，**和弦完全不变**，只有贝斯和旋律换了 → 整首歌和声错位、不协和。
- `bass.py` 里 `base_roots` 只有 4 个键，换任何新和弦 → `KeyError`。
- 两份数据将来必然漂移。

**修法**：删掉 `chords.py` 里的三份重复定义，改为 `from core.theory import CHORDS, PROGRESSION, note_name_to_midi`；根音统一用 `note_name_to_midi()` 算，不要手写 MIDI 数字。

### P0-2 `compose.sh` 不转发版本号 → 每次覆盖 v1，违反硬规则 3

```
$ bash tools/compose.sh projects/demo --version v2
生成完成: projects/demo/music/output/demo-v1.mid   ← 还是 v1
$ ls projects/demo/music/output/
demo-v1.mid                                        ← 只有一份
```

脚本只传了 `--project`，`--version` 被吞掉。硬规则 3 说「不覆盖历史，-v1 -v2」，但**当前没有任何命令能产出 v2**。
README 里「改完重跑 compose.sh，版本号 +1」是句空话。

**修法**：
```bash
VERSION="${2:-auto}"
if [ "$VERSION" = "auto" ]; then
  LAST=$(ls "$PROJECT_DIR"/music/output/*-v*.mid 2>/dev/null \
        | sed -E 's/.*-v([0-9]+)\.mid/\1/' | sort -n | tail -1)
  VERSION="v$(( ${LAST:-0} + 1 ))"
fi
python music/core/compose.py --project "$PROJECT_DIR" --version "$VERSION"
```

### P0-3 全局 config.py 让「创作隔离」名存实亡

硬规则 1：每首歌独立目录、独立窗口。但 `music/core/config.py` 是**全项目唯一一份**。
后果：你做第二首歌改了 BPM / 调性 / section，`demo-v1.mid` **再也生成不出来**。所谓"版本化、可回滚"只回滚了文件名的后缀。

这不是风格问题，是硬规则 1 与实现的结构性冲突。

**修法**（最小改动）：配置下沉到项目内，并随版本快照。

```
projects/demo/
├── brief.md
├── config.json          ← 本项目唯一参数源
└── music/output/
    ├── demo-v1.mid
    └── demo-v1.config.json   ← 生成时快照，保证 v1 永久可复现
```
`compose.py` 里 `load_config(project_dir)`：有 `config.json` 就用它覆盖 `DEFAULT_CONFIG`，没有就回退默认值并在 stdout 警告。生成完把实际生效的 config 一起写进 output。

### P0-4 贝斯音高硬编码错了，四个和弦还跨了八度

`bass.py` 第 7 行：
```python
base_roots = {"F#m":57,"D":50,"A":45,"E":52}
```
实测产物：
```
bass range=45~57    首音: A3 A3 A3 A3 | D3 D3 D3 D3 | ...
chords range=50~64  bar1 和弦音: F#3 A3 C#4
```

三个问题：

1. **57 是 A3，不是 F#**。F#m 的根音应该是 `F#2 = 42` 或 `F#3 = 54`。57 是这个和弦的**三音**，等于全曲第一小节贝斯就在弹和弦三音，根音丢失。
2. **八度完全不统一**：57 / 50 / 45 / 52 —— 相邻差 -7 / -5 / +7，贝斯线在乱跳，不是走向。
3. **A3 (57) 与和弦里的 A3 完全同音同八度**——低频直接内耗，Logic 里必须重写整个贝斯。

另外 `root_octave=1` 这个参数传进来**从头到尾没用过**，是个骗人的接口。

**修法**：定一个明确音区（贝斯统一 E1~G2 区间），根音由和弦名推导：
```python
from core.theory import PROGRESSION, note_name_to_midi

def _bass_root(chord: str, octave: int = 2) -> int:
    name = chord[:-1] if chord.endswith("m") else chord
    p = note_name_to_midi(name, octave)     # F#2=42, D2=38, A1=33→统一到2八度
    while p > 45:  p -= 12                 # 夹到 A1~A2 区间，避免上下乱窜
    while p < 33:  p += 12
    return p
```

### P0-5 `agents.md` 指向一个不存在的脚本

常用命令第 3 条：`bash tools/synthesize.sh music/output/<file>.mid` —— **该文件不存在**。
skill 与规则里写不存在的命令，等于给未来的自己（或任何接手的 agent）埋一个必踩的坑。

**修法**：要么补上（用 `pretty_midi` + `sf2` 或直接 `afplay` 前先 `fluidsynth`），要么删掉这一行。

---

## 三、P1：音乐层面（决定这东西能不能用）

### P1-1 `outro` 4 小节是完全空白

config 里 `sections` 写了 24 小节，实测音符只到 **19.92 小节**：
```
duration: 56.93s = 19.92 bars   ← intro4 + verse8 + chorus8 = 20，outro 0
```
`compose.py` 的小节计数推进了，但 `if section in ("intro","verse","chorus")` 白名单把 outro 直接跳过，**没有任何音符**。

顺带：这个白名单意味着你在 config 里加 `"bridge": 8`，会**静默失败**（不报错、不出音）。

### P1-2 `pad` 是空轨，`arp` 根本不存在

- `compose.py` 建了 `pad` instrument，**从来没有调用任何 pad builder**。MIDI 里这条 track 存在但 0 个音符。
- README 承诺「5 轨自动分离」，硬规则 4 的音轨名列表里有 `arp` —— 代码里**没有 arp 模块**。

### P1-3 三个 section 用同一套织体，没有动态层次

`intro` / `verse` / `chorus` 三个分支里，chords / bass / drums **调用完全相同的函数**，唯一区别是 `chorus` 多了一条 lead。
结果：前奏第一拍就是满编鼓 + 满贝斯。

这跟你 `USER.md` 里写的「电影感、留白、副歌有记忆点」**是直接矛盾的**——现在的产物既没有留白，副歌也没有"起来"，因为它从第 1 秒就已经在顶了。

**修法**：用编排矩阵驱动，别用 if 白名单。

```python
ARRANGE = {
    #               chords  bass  drums      lead  pad   vel_scale
    "intro":  dict(chords=1, bass=0, drums=None,    lead=0, pad=1, vel=0.70),
    "verse":  dict(chords=1, bass=1, drums="half",  lead=0, pad=1, vel=0.85),
    "chorus": dict(chords=1, bass=1, drums="full",  lead=1, pad=1, vel=1.00),
    "outro":  dict(chords=1, bass=0, drums=None,    lead=0, pad=1, vel=0.65),
    "bridge": dict(chords=1, bass=1, drums="hat",   lead=0, pad=1, vel=0.80),
}
```
所有 pattern 接收 `vel_scale`，鼓接收 `density`（`None/half/full`）。这样加 section 只加一行字典，不会静默失败。

### P1-4 config 里一半参数是装饰性的

| 参数 | 声明值 | 实际是否生效 | 证据 |
|---|---|---|---|
| `bpm` | 84 | ✅ | 产物 tempo=84 |
| `key` | "F#m" | ❌ | 全代码无引用，和弦写死在 progression 里 |
| `time_sig` | (4,4) | ❌ | 从未写入 MIDI；`bar_len = 4*beat` 在 4 个 pattern 里各自硬编码 |
| `swing` | 0.0 | ❌ | 无任何引用 |
| `velocity_base` | 80 | ❌ | 力度全是 55/90/85/100/45 硬编码 |

改了没反应的参数比没有参数更危险——下次你（或 AI）会以为调过了。

### P1-5 力度全是常量，机械感重

```
drums vel=[45, 80, 100]   chords vel=[55]   bass vel=[90]   lead vel=[85]
```
每轨全程一个力度值，没有 accent、没有强弱拍差、没有段落渐变。
这类 MIDI 拖进 Logic，**每个音符都要重画力度**，"在 Logic 精修"就变成了"在 Logic 重做"。

最低成本改法：力度 = `base * section_scale * accent(强拍1.0 / 弱拍0.85) + humanize(±4, 需要 seed)`。

### P1-6 lead 不跟和弦走，动机永远一样

```python
root = 69  # A4 起手，写死
motif = [0, 7, 12, 7]  # 永远一样
```
- 在 F#m 上 A4 是三音（可以），在 D 上 A4 是五音（可以），但在 **E 上 A4 是四度** → 挂留/冲突，没有解决。
- 8 小节副歌只有 2 个动机（`i % 2 == 1` 时 `continue` 留白），第 3、4 次重复一模一样，**"有记忆点"变成了"有重复"**。
- 说好的「留白 ≥40%」：真正播放的小节里是 4 拍 4 个音，密度 100%。

**修法**：动机按和弦取音级（chord tone map），第 2 次重复做变奏（改尾音 / 加经过音 / 节奏移位），最后 2 小节加一个上扬尾句。

### P1-7 和弦全部原位、挤在一个八度里

`range=50~64`（D3~E4），全部 root position 三和弦，8 小节完全一样的排列。
- 没有转位 → 声部跳进大，听感"硬"。
- 没有 open voicing → 中频糊成一团，跟贝斯抢。
- 三和弦没有 7 音 / 9 音 / sus → 跟你「电影感」的定位不匹配。

**修法**：给和弦加 voicing 层——`[0, 7, 12, 15]` 之类的开放排列，加一个 `voice_lead()` 选与前一个和弦共同音最多的转位，chorus 加 9 音或 sus4。

### P1-8 鼓每小节一模一样，intro 也是满鼓

kick 1/3、snare 2/4、8 分 hat —— 24 小节零变化。
- 没有 fill（第 8 小节进副歌前应该有个 tom fill）
- 没有 crash / open hat（`GM_DRUM` 里定义了 `openhat` / `clap` / `tom1`，**一次没用**）
- intro 满鼓 → 你的「留白」直接没了

### P1-9 `resolution=220`

```
ticks_per_beat: 220
```
pretty_midi 默认 220，Logic 默认 480/960。非整数倍的 PPQ 在导入时会让 16 分/三连音产生微小量化误差。

**修法**：`pretty_midi.PrettyMIDI(initial_tempo=bpm, resolution=960)`，一行。

---

## 四、P2：工程化缺口

| # | 问题 | 说明 |
|---|---|---|
| 1 | **brief.md 与 config.py 断链** | 5 个 skill 的流程起点都是 `brief.md`，但代码只读全局 `config.py`。brief 里的 bpm/key/sections 要人肉/AI 手抄进 config —— 抄错就没人知道。`projects/demo/` 里连 brief.md 都不存在。 |
| 2 | **没有 `decisions.md`** | 硬规则 3 要求「decisions.md 记录每次决策」，文件不存在。`midi-iterate` skill 第 1 步「读 decisions.md」必然落空。 |
| 3 | **不是 git 仓库** | `git status` → `fatal: not a git repository`。所谓"可回滚"只有文件名后缀，没有真正的版本历史。 |
| 4 | **没有 `.gitignore`** | `venv/` 758 个文件、`.DS_Store`、`__pycache__/*.pyc` 全在根目录，一旦 `git init` 全部入库。 |
| 5 | **生成后无任何校验** | 只 `print("生成完成:", path)`。不报小节数、轨道数、音域、时长、是否有空轨。P1-1/P1-2 这类问题只能开 Logic 才发现。应该有个 `--report` 打印每轨 notes/range/bars，并断言「无空轨」「总小节数 == config 求和」。 |
| 6 | **四个 pattern 参数签名不一致** | `chords.build(base_octave=3)`、`bass.build(root_octave=1)` 未使用、`drums.build()` 无力度参数。加一层需要改 4 个文件。应统一 `build(inst, ctx)`，`ctx` 携带 bpm/bar/beats/vel_scale/key。 |
| 7 | **sys.path hack** | `sys.path.insert` 靠 `__file__` 反推，脆弱。改成 `PYTHONPATH=music python -m core.compose`，或加 `pyproject.toml`。 |
| 8 | **init_env.sh 与 requirements.txt 漂移** | 脚本里 `pip install pretty_midi mido numpy` 硬编码，不用 `-r requirements.txt`；且 `pip freeze \| grep` 生成 requirements 与手写目标不一致。 |
| 9 | **无 take/seed 机制** | 现在是确定性的（好），但没法「同一版连出 3 个 variation」。config 里加 `seed`，pattern 里用 `random.Random(seed)`。 |
| 10 | **无用代码** | `config.ROOT` 未使用；`theory.note_name_to_midi` 未使用（而 chords 又自己实现了一遍）。 |
| 11 | **skill 与代码不同步** | `midi-compose/SKILL.md` 写「主入口 music/compose.py」，实际是 `music/core/compose.py`；写「默认量化 1/16」而代码无量化逻辑。 |
| 12 | **无 docstring / 无 type hints** | 函数签名基本靠猜（`build(chord_inst, bpm, start_bar, num_bars, base_octave=3)`），对"AI 下一轮接手"极不友好——而这恰好是本项目的核心使用场景。 |

---

## 五、建议的目标结构

```
music_arrangement/
├── agents.md
├── pyproject.toml                # 新增：包化，去掉 sys.path hack
├── music/
│   ├── core/
│   │   ├── theory.py             # 唯一音高/和弦/鼓映射源
│   │   ├── config.py             # 默认值 + load_config(project_dir)
│   │   ├── arrange.py            # 新增：ARRANGE 矩阵，section → 轨道开关
│   │   ├── voicing.py            # 新增：转位与 voice leading
│   │   └── compose.py            # 只做编排调度 + 写出 + 校验报告
│   └── patterns/
│       ├── chords.py             # from core.theory import ...
│       ├── bass.py
│       ├── drums.py              # 接 density: none/half/full
│       ├── lead.py               # 接和弦音级
│       ├── pad.py                # 新增（现在是空轨）
│       └── arp.py                # 新增（agents.md 承诺了）
├── projects/<date>-<style>-<seq>/
│   ├── brief.md
│   ├── config.json               # 本项目唯一参数源
│   ├── decisions.md
│   └── music/output/
│       ├── <name>-v1.mid
│       └── <name>-v1.config.json # 版本快照
└── tools/
    ├── init_env.sh               # 改成 pip install -r requirements.txt
    ├── compose.sh                # 转发 --version，默认自增
    └── check_midi.py             # 新增：产物体检（空轨/小节数/音域/PPQ）
```

---

## 六、行动清单

**今天（30 分钟内，都是几行的事）**
1. `compose.sh` 转发 `--version` 并默认自增 —— 否则你今晚就可能覆盖掉唯一一版。
2. `chords.py` 删掉重复定义，改 `from core.theory import`。
3. `bass.py` 的 `base_roots` 换成 `note_name_to_midi` 推导，统一音区。
4. `PrettyMIDI(..., resolution=960)`。
5. 删掉或补上 `tools/synthesize.sh` 那一行。

**本周（把"能听"变成"可控"）**
6. `ARRANGE` 矩阵 + `vel_scale`，先解决 intro 满鼓和 outro 空 4 小节。
7. 配置下沉到 `projects/<dir>/config.json` + 版本快照。
8. `--report` 体检输出（轨道数/音域/小节数/空轨告警）。
9. `git init` + `.gitignore` + `decisions.md` 模板。

**下一轮（音乐质量）**
10. 和弦 voicing / 转位 / 9 音。
11. lead 跟和弦音级 + 动机变奏。
12. 鼓 fill / crash / density 分层。
13. `pad.py` 与 `arp.py` 补齐。

---

## 附：验证记录

```
生成产物: projects/demo/music/output/demo-v1.mid (2658 bytes)
format: 1   tracks: 6   ticks_per_beat: 220
  track1: chords  ch 0  notes=60  range F#3~E4  vel=[55]
  track2: bass    ch 1  notes=80  range A2~A3   vel=[90]   首音 A3（应为 F#）
  track3: lead    ch 2  notes=16  range A4~A5   vel=[85]
  track4: drums   ch 9  notes=240 range 36~42   vel=[45,80,100]
  track5: pad     ch 4  notes=0   ← 空轨
时长 56.93s = 19.92 小节（config 声明 24 小节，outro 空白）
```

`--version v2` 传入后仍输出 `demo-v1.mid`（P0-2 已复现）。
修改 theory.PROGRESSION 后 chords 不变、bass KeyError（P0-1 已复现）。

---

## 附录二：P0 修复记录

| 编号 | 改动文件 | 做法 | 验证 |
|---|---|---|---|
| P0-1 | `music/patterns/chords.py` | 删除本地重复的 `CHORDS/PROGRESSION/NOTE_OFFSET`，改为 `from core.theory import ...` | `C.PROGRESSION is T.PROGRESSION` → True |
| P0-2 | `tools/compose.sh` | 转发版本号；支持 `v3` / `--version v3`；缺省扫描已有产物取 max+1 | 首跑输出 `demo-v2.mid`，`demo-v1.mid` 保留 |
| P0-4 | `music/patterns/bass.py` | 去掉 `base_roots` 硬编码，改 `_bass_root()` 由和弦名推导并折进 A1~G#2；启用 `root_octave` | 贝斯 F#2/D2/A1/E2，与和弦根音一一对齐，音域 33~42 |
| P1-9 | `music/core/compose.py` | `PrettyMIDI(..., resolution=960)` | PPQ 由 220 → 960 |
| P0-5 | `agents.md` | 删掉不存在的 `tools/synthesize.sh`，改为「拖进 Logic 试听」+ 版本用法 | 文档内命令全部可执行 |

回归后的 `demo-v2.mid`：

```
format=1 tracks=6 PPQ=960
chords 60 音  D3~E4      bass 80 音  A1~F#2
lead   16 音  A4~A5      drums 240 音 C2~F#2
bar1 F#m 贝斯 F#2 和弦 F#3 A3 C#4
bar2 D   贝斯 D2  和弦 D3 F#3 A3
bar3 A   贝斯 A1  和弦 A3 C#4 E4
bar4 E   贝斯 E2  和弦 E3 G#3 B3
```

换调测试（theory 改为 Am-F-C-G）：和弦跟随、贝斯跟随、无 KeyError。

**仍未处理**：和弦转位/voice leading、swing、arp 轨、brief→config 自动化。

---

## 附录三：第二轮改造记录（编排矩阵 / 配置下沉 / 产物体检）

### 1. 编排矩阵 `music/core/arrange.py`（新）

`ARRANGE` 表决定每段的轨开关、鼓密度、力度缩放，替代原来的 `if section in (...)` 白名单。

```
段落     chords bass drums lead pad  力度
intro    ✓      —    —     —    ✓    0.70
verse    ✓      ✓    half  —    ✓    0.85
chorus   ✓      ✓    full  ✓    ✓    1.00
bridge   ✓      ✓    hat   —    ✓    0.80
outro    ✓      —    —     —    ✓    0.65
```

未定义段落直接报错，不再静默丢整段：

```
$ bash tools/compose.sh projects/<x>
[配置错误] 未知段落 'drop'：请先在 music/core/arrange.py 的 ARRANGE 中定义
           （已支持: intro, verse, chorus, bridge, outro）
```

同时修掉：**outro 4 小节空白**、**intro 第一拍就满编鼓**、**段落之间没有动态差**。

### 2. 配置下沉 `projects/<dir>/config.json`（新）

`load_config(project_dir)` 优先读项目内 JSON，缺省才回退 `DEFAULT_CONFIG` 并告警。
每版生成后自动写 `<name>-vN.config.json` 快照，旧版本永久可复现。

顺带让「装饰性参数」不再骗人：

| 参数 | 处理 |
|---|---|
| `velocity_base` | 真的生效了：作为主控力度（80 为基准）乘进所有轨 |
| `swing` | 未实现 → 写非 0 直接报错，而不是默默忽略 |
| `time_sig` | 只支持 4/4 → 写 3/4 直接报错 |
| `key` | 仍只作记录，每次生成都会打印「key 仅记录，和弦由 PROGRESSION 决定」 |

隔离验证：新建一个 `bpm=128 / 5 段落` 的项目，生成正常，`demo` 的 v1/v2 字节未变。

### 3. 产物体检 `music/core/report.py` + `tools/check.sh`（新）

`compose.sh` 生成后自动跑；也可单独跑。检查项：

- format 是否为 1、PPQ 是否为 960
- 每轨音符数 / 音域 / 力度区间 / 结束小节
- 空轨（应为空却被写进文件、或按编排该有音却没音）
- 鼓轨是否落在 channel 10
- 实际小节数 vs config 声明
- **逐段检查是否有音符**、BPM 是否与 config 一致
- 各轨音域是否明显超出角色定位（提示级）

拿原始 v1 试跑，四条历史问题全被抓出来：

```
[失败] 体检未通过:
  - PPQ=220，应为 960（与 Logic 默认对齐）
  - 实际 19.92 小节 ≠ config 声明 24 小节
  - 段落 'outro'（第 21~24 小节）没有任何音符
  - 以下轨按编排应有音符但实际为空: ['pad']
```

### 4. 顺带修掉的 P1

- **pad 空轨 → `patterns/pad.py`**：开放五度堆叠（8 度/12 度/2 个 8 度），不叠三音，避免中频糊。
- **鼓零变化 → 三档密度**：`hat` / `half` / `full`；四小节一次桶鼓过门；段落起点吊镲；正拍重反拍轻。
- **lead 不跟和弦 → 按和弦音级取音**：动机改成 `根-三-五-三` / `根-五-八-五`，
  起手音取「离 A4 最近的和弦内音」。
  实测 v4 的 28 个旋律音 **全部落在和弦上**。
  （v3 是中间态：动机用固定半音 `+15` 在 A 大三和弦上得到 C5，与 C# 冲突，已被 v4 取代。）
- **旋律只覆盖 2 个和弦**：原来 `i % 2` 跳过与 4 小节进行的奇偶周期相同，
  D / E 整段没旋律；改成每 4 小节留一小节双长音呼吸，四个和弦都有旋律。
- **力度全常量 → 段落缩放 + 正反拍 accent**。

### 5. 改造过程中新发现并修掉的 bug（自己上一轮引入）

`compose.sh` 里 `set -o pipefail` + `ls "$OUT_DIR"/*-v*.mid`：
`ls` 匹配不到文件时返回非 0，pipefail 让整条管道失败，`set -e` 直接退出 ——
**全新项目第一次生成会静默失败（退出码 1，无任何输出）**，README 的「新增一首歌」根本跑不通。
改用 `find`（找不到也返回 0）。

### 回归数据（demo-v4.mid）

```
format=1  PPQ=960  BPM=84  24.00 小节  5 轨

段      小节      chords bass drums lead pad
intro   1-4         12    0     0     0   12
verse   5-12        24   32    80     0   24
chorus  13-20       24   32   111    28   24
outro   21-24       12    0     0     0   12
```

副歌 28 个旋律音 100% 落在当小节和弦音上；吊镲在 bar13 进，桶鼓过门在 bar16 / bar20。


