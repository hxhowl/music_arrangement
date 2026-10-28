# 审核：能不能只靠"描述"做一份全新编曲？

日期：2026-10-28
方法：通读全部代码与文档 + 端到端实验（两种截然不同的描述 → 对比产物音符骨架）

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
