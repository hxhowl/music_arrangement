# 审核：能不能只靠"描述"做一份全新编曲？

日期：2026-10-28
方法：通读全部代码与文档 + 端到端实验（两种截然不同的描述 → 对比产物音符骨架）

> **状态更新（2026-10-28 23:15）**
> 本文提出的四个断点已修三个（和弦/调性、风格库、新建项目脚手架），
> 第四个（skill 未注册）用 `agents.md` 的标准流程兜底。
> 下面保留原始审核内容作为问题记录，修复细节见文末「附录：改造结果」。

## 结论

**能做「新的一版」，做不了「新的编曲」。**

今天的链路，描述能改的是 **速度、段落长度、各段稀疏程度**；
改不动的是 **调性、和弦进行、律动、织体、旋律性格** —— 这五项恰好构成"一首歌听起来像不像另一首歌"。

换句话说：你换一句话描述，拿到的仍然是同一首歌的不同长度和速度。

## 实验证据

建两个项目，配置故意差到不能再远：

| | a-sad | b-fast |
|---|---|---|
| bpm | 60 | 150 |
| key | Am | C |
| 段落 | intro4 / verse8 / outro4 | intro4 / chorus12 / outro2 |

产物每小节正拍的和弦音与贝斯音：

```
和弦音  a-sad : 50 50 50 50 | 52 52 52 52 | 54 54 54 54   ← D3 E3 F#3
        b-fast: 50 50 50 50 | 50 52 52 52 | 52 54 54 54   ← 同样 D3 E3 F#3
贝斯    a-sad : 33 33 38 38 40 40 42 42                    ← A1 D2 E2 F#2
        b-fast: 33 33 33 38 38 38 40 40                    ← 同一条线
```

**key 写了 Am 和 C，和弦却都是 F#m–D–A–E。** 原因是 `PROGRESSION` 写死在
`music/core/theory.py:12`，四个 pattern 全部直接 `from core.theory import PROGRESSION`，
config 里的 `key` 从来没有参与过生成（生成时会打印一行 `[info] key 仅作记录` 提醒）。

## 描述现在能控制什么

| 描述里的维度 | 现状 | 落点 |
|---|---|---|
| 速度（"慢一点/快一点"） | ✅ 生效 | `config.json` → `bpm` |
| 时长 / 段落结构（"90 秒""副歌长一点"） | ✅ 生效 | `config.json` → `sections` |
| 各段密度（"前奏留白""副歌堆起来"） | ✅ 生效 | `arrange.py` → `ARRANGE` |
| 整体力度 | ✅ 生效 | `config.json` → `velocity_base` |
| **调性**（"a 小调""大调明亮一点"） | ❌ 无效 | 写了不影响任何音 |
| **和弦进行**（"想用卡农""要 i-VI-III-VII"） | ❌ 无效 | 写死在 `theory.py` |
| **风格 / 律动**（"bossa""half-time""进行曲"） | ❌ 无此字段 | bass 全曲四分音符，鼓只有三档密度 |
| **旋律性格**（"要有记忆点的动机"） | ❌ 固定 | `lead.py` 的 `MOTIF` 全套唯一 |
| 乐器编制 | ❌ 固定 5 轨 | `compose.py` 的 `TRACKS` |
| 音色 | — | 本来就该在 Logic 里定 |

## 四个断点（按严重度）

### 断点 1：和弦进行还在全局，一首歌换和弦会改掉所有歌（致命）

配置下沉只下沉了 bpm / sections / velocity_base，**最核心的音乐参数（和弦进行）仍然是全局的**。
`music/core/theory.py:12: PROGRESSION = ["F#m", "D", "A", "E"]`，四个 pattern 直接引用。

后果：给新歌换一套和弦，`demo-v4.mid` 就再也生成不出来了 —— 违反硬规则 1（创作隔离）。
这和上一轮修掉的"全局 config"是同一个病，只是藏得更深。

### 断点 2：只有一套织体，没有"风格"这个概念（致命）

- `bass.py`：全曲每拍一个根音，四种和弦一律如此
- `drums.py`：hat / half / full 三档，本质是同一个 4/4 摇滚底鼓
- `lead.py`：`MOTIF = (0,1,2,1)` 一套动机用到底
- `pad.py`：开放五度堆叠一套

所以"悲伤钢琴小品"和"欢快亲子"会拿到同一套节奏型。这不是参数没调好，
是**代码里不存在第二个选项**。

### 断点 3：brief.md 没有代码消费，skill 也没被加载（流程断裂）

- 全项目只有 `config.py` 的一行注释提到 brief，**没有任何代码读它**。
  brief 是给人看的，`bpm/key/sections` 要人手抄进 `config.json`。
- 实测：四个 skill（song-brief / midi-compose / midi-iterate / logic-import）
  目录、frontmatter 都合法，但在当前会话里调用直接报 `Can not find skill: "song-brief"`。
  也就是说**触发层没接上**，用户说"帮我起一首歌"时不会自动走 song-brief 的流程。

### 断点 4：没有"新项目"生成器（次要）

新建项目要手写 `config.json`（虽然只有 6 个字段）。写错键名/漏 sections 会报错，
但更常见的是**忘记复制 config.json** —— 于是静默落回默认值，音乐悄悄变了。

## 最小改造方案（三步，可增量做）

### 第 1 步：让调性与和弦进行真正生效（改 3 个文件，约 80 行）

把和弦进行从"绝对音名"改成"级数"，由 `key` 推导：

```python
# theory.py
SCALES = {"major": [0,2,4,5,7,9,11], "minor": [0,2,3,5,7,8,10]}
ROMAN = {"i":0, "ii":1, "III":2, "iv":3, "v":4, "VI":5, "VII":6, "I":0, "IV":3, "V":4}

def chord_from_degree(key: str, degree: str, mode: str) -> str:
    """key="Am", degree="i" -> "Am"；key="C", degree="VI" -> "Am" """
```
`config.json` 增加 `"progression": ["i", "VI", "III", "VII"]`，`theory` 保留默认值。
效果：**同一句"做一首 a 小调"，和弦立刻跟着变**，且换歌不再污染其它项目。

### 第 2 步：加 `style` 维度 + 2~3 套律动（改 4 个 pattern）

`config.json` 加 `"style": "cinematic" | "pop" | "lofi"`，
每个 pattern 按 style 取一套参数（音符密度、切分位置、音区、动机形状）。

先做三套就够覆盖你的使用场景（USER.md：电影感 + 无厘头反差）：

| style | bass | drums | lead |
|---|---|---|---|
| cinematic | 全音符长音 | 无鼓或只有心跳底鼓 | 长音 + 大跳 |
| pop | 八分音符根音+五度 | 标准 4/4，2/4 军鼓 | 级进动机 |
| lofi | 切分 + 休止 | 半拍 + swing hat | 短句 + 重复 |

### 第 3 步：`tools/new_song.py`（约 40 行）

```
python tools/new_song.py "90秒 亲子 电影感 结尾反差" --bpm 84 --key Am \
    --style cinematic --sections intro8,verse16,chorus16,outro8
```
一条命令生成 `projects/<date>-<slug>/`、`brief.md`、`config.json`，
不再手抄参数、不会再忘配 config。

做完这三步，流程才真的是「一句话 → 一首有明确性格的编曲」。

## 在此之前，现实可用的工作流

1. `mkdir -p projects/<date>-<style>-<seq>/music/output`
2. `cp projects/demo/config.json projects/<date>-.../`
3. 改 `config.json` 的 `bpm` / `sections`（`key` 先别改，改了也没用）
4. **想换和弦/律动，必须直接改 `music/core/theory.py` 与 `music/patterns/*.py`**
   —— 注意这会影响所有项目，改前先 `git commit`，出完 MIDI 再 `git checkout` 还原
5. `bash tools/compose.sh projects/<dir>`，看体检
6. 拖进 Logic 换音色

第 4 步是目前最大的坑：**它不是"给新歌换和弦"，是"临时改写整条产线"**。

---

## 附录：改造结果（2026-10-28 23:15）

三步全部落地，四个断点修了三个，第四个用文档兜底。

### 断点 1（和弦/调性）→ 已修

和弦改成 **`key` + 级数** 推导：

```
"key": "Am",  "progression": ["i","VI","III","VII"]   →  Am - F - C - G
"key": "Dm",  "progression": ["i","VI","III","VII"]   →  Dm - Bb - F - C
"key": "C",   "progression": ["I","V","vi","IV"]      →  C - G - Am - F
"key": "Bb",  "progression": ["I","vi","IV","V"]      →  Bb - Gm - Eb - F
```

`PROGRESSION` 全局常量已删除，pattern 通过 `Ctx` 拿到本曲的和弦。
和弦名按调号拼写（D 小调的 VI 级是 `Bb`，不是 `A#`）。

旧行为保持不变：`F#m` + `i-VI-III-VII` 仍然推出 `F#m-D-A-E`。

### 断点 2（只有一套织体）→ 已修

新增 `music/core/styles.py`，四套风格，与段落编排正交：

| 风格 | 贝斯（第 1 小节拍位） | 副歌鼓 | 副歌旋律 |
|---|---|---|---|
| cinematic | `0.0`（全音符） | 3 个音，心跳 | 2 个长音 A4→E5 |
| pop | `0, 1, 2, 2.5(五度), 3` | 9 个音，标准 4/4 | 4 音级进 A4-C5-E5-C5 |
| lofi | `0, 0.75, 1.5, 2.5(五度)` | 9 个音，半拍 | 4 音切分 A4-C5-C5-E5 |
| playful | `0, 0.5(八度), 2, 2.75(五度)` | 8 个音，错位重音 | 5 音跳进 C5-A5-E5-C5-A5 |

同一份 `ARRANGE`（verse=medium / chorus=full）在四种风格下得到四套完全不同的律动，
且段落结构不变。

### 断点 3（brief 无消费 / skill 未注册）→ 部分修

- `tools/new_song.sh` 现在**直接生成 brief.md + config.json + decisions.md**，
  brief 不再是给不了代码的孤儿文档。
- 四个 skill 依然没有在本会话注册（`Can not find skill`）。
  兜底方案：`agents.md` 里写了一份「标准流程」，与 skill 内容一致，
  即使 skill 不加载，AI 读到 agents.md 也知道该怎么走。

**建议你验证一次**：开一个新对话窗口说「帮我做一首 60 秒的配乐」，
看它是走 `new_song.sh` 还是自己乱来。若仍不加载 skill，可把
`.workbuddy/skills/` 复制到 `~/.workbuddy/skills/`（用户级，跨项目可用）。

### 断点 4（无脚手架）→ 已修

```bash
bash tools/new_song.sh "60秒 亲子短视频 电影感 慢" --duration 60 --key Am
```

- 从描述关键词推断风格与 BPM，并打印推断依据；描述里命中多种风格会主动提示
- `--duration` 自动反推段落（前奏 15% / 主歌 38% / 副歌 35% / 尾奏 12%）
- 段落名、风格名、调性写错都会在写文件前报错

实测：`--duration 60 --key Am` → 72bpm / 18 小节 / 60.0 秒 / `Am-F-C-G`，体检通过。

### 现在的真实能力边界

**能**：一句话出项目 → 出 MIDI；换风格、换调、换和弦进行、换段落结构；每版可复现。
**仍不能**：段内混搭风格（前奏 cinematic、副歌 playful）；转位与 voice leading；
swing；arp 轨；人声。

