# 导入 Logic 后，乐器怎么对

这份是针对"生成出来的 MIDI 拖进 Logic，音色不对劲"这个具体问题的对照参考。
数字全部来自本机导出（见 [gm-programs.md](gm-programs.md) 与 [logic-patches.md](logic-patches.md)）。

---

## 一、先说清楚三件事，否则会一直觉得"怎么都不对"

| 你可能以为 | 实际发生 |
|---|---|
| MIDI 里记着"弦乐群"这个乐器 | **MIDI 里没有乐器**，只有 program 号（0~127）和通道号。你看到的乐器名，是软件拿 program 号去查 GM 表翻译出来的 |
| Logic 会去我的音色库里找对应的音色 | **不会**。它用的是 macOS 自带的 GM 音色库（`gs_instruments.dls`），跟 Logic 音色库是两套东西 |
| 鼓那条轨也是选音色 | 不一样。通道 10 上 program 号选的是**鼓组**（Standard / Room / Power…），不是音色 |

所以"对不上"通常不是 bug，是三件事叠在一起：

1. **名字对不上**：我们叫 `chords=弦乐群`，GM 表里 48 号叫 `Strings`；
2. **音色对不上**：GM 的音色是"能发对音高的最低保障"，不是 Logic 那些几百 MB 的采样；
3. **鼓组例外**：program 号在通道 10 换了含义，而且 Logic 的 Drum Machine Designer **不理** program 号。

---

## 二、Logic 打开 `.mid` 时到底做了什么

大致是这三步（不同版本菜单叫法略有差异）：

1. 按 MIDI 里的 program 号，给每条轨建一个软件乐器轨，加载 GM 音色；
2. 轨道名取 GM 音色名（所以你会看到 `Piano 1`、`Strings` 这种，而不是我们的 `chords`）；
3. 通道 10 的轨按 program 号选 GM 鼓组；其他轨按普通音色处理。

**它不会**：去你的 Library 里挑一个"更好的弦乐"。这一步必须你做。

---

## 三、正确姿势（四步）

1. **导入**：把 `<name>-vN.mid` 拖进 Logic 空白工程，或 `文件 > 打开` 选它。
2. **改名**：按 `chords / bass / drums / perc / arp / lead / counter / pad` 把轨道重命名 ——
   跟工程里的槽名对齐，后面调参数、对照体检报告都用得上。
3. **换音色**：逐轨在 Library 面板里换（搜索词见第四节）。这一步是"创作"，不是"修复"。
4. **存模板**：`文件 > 存储为模板`，下次导入后直接套这套 channel strip，不用重来。

---

## 四、逐槽对照表

「Logic 里搜什么」是关键词建议，不是唯一答案；本机实际有哪些候选见
[logic-patches.md](logic-patches.md) 最后一节。

### chords（和声层）

| 我们叫 | 号 | GM 名 | Logic 里搜什么 | 换的时候注意 |
|---|---:|---|---|---|
| `piano` | 0 | Piano 1 | `grand` / `upright` / `felt` | 最容易"一听就对"的一档 |
| `epiano` | 4 | E.Piano 1 | `rhodes` / `wurli` / `electric piano` | lofi 必备，会自带一点噪声 |
| `nylon` | 24 | Nylon-str.Gt | `nylon` / `acoustic guitar` | 我们生成的是柱式和弦，真实吉他要用扫弦才像 |
| `steel` | 25 | Steel-str.Gt | `steel` / `acoustic guitar` | 同上，建议只当铺底 |
| `strings` | 48 | Strings | `strings` / `ensemble` | 长音要拉满，我们已把 hold 调到 0.99 |
| `organ` | 16 | Organ 1 | `organ` / `b3` | 铺满不换气，别加 release 太长的 |

### bass（低音）

| 我们叫 | 号 | GM 名 | Logic 里搜什么 |
|---|---:|---|---|
| `finger` | 33 | Fingered Bs. | `electric bass` / `finger` |
| `pick` | 34 | Picked Bs. | `pick` / `rock bass` |
| `upright` | 32 | Acoustic Bs. | `upright` / `double bass` |
| `synth` | 38 | Synth Bass 1 | `synth bass` / `sub` |

### drums（鼓组）

通道 10。号选的是**鼓组**，不是音色：

| 我们叫 | 号 | 本机鼓组名 | Logic 里 |
|---|---:|---|---|
| `standard` | 0 | Standard | `Acoustic Drums` 里任选一套 |
| `room` | 8 | Room | 同上，挑"房间感"重的 |
| `power` | 16 | Power | 找 rock / heavy 那类 |
| `electronic` | 24 | Electronic | `Electronic Drums`（808 / trap 类） |
| `brush` | 40 | Brush | 找 brush / jazz 那类，lofi 常用 |

> **重要**：用 Drum Machine Designer 时，program 号无效，必须在 DMD 里手动选 kit。
> 这也是"鼓永远对不上"的最常见原因。

### perc（装饰打击）

`perc` 没有自己的 program，它跟随 `drums` 的鼓组；换的是**打哪个部件**：

| 我们叫 | 实际改的是 | 说明 |
|---|---|---|
| `shaker` | 音符号 70 | 沙锤，最百搭 |
| `tambourine` | 54 | 铃鼓，正拍更亮 |
| `rim` | 37 | 鼓边侧击 |
| `congas` | 61~63 | 康加，拉丁 / 亲子 |
| `clap` | 39 | 拍手，短视频常用 |

在 Logic 里建议单独一条轨、单独加载一个 Percussion 类音色，别和 drums 挤同一条。

### arp（琶音）

| 我们叫 | 号 | GM 名 | Logic 里搜什么 |
|---|---:|---|---|
| `synth` | 81 | Saw Wave | `arp` / `sequence` |
| `pluck` | 45 | PizzicatoStr | `pizzicato` / `pluck` |
| `harp` | 46 | Harp | `harp` |
| `marimba` | 12 | Marimba | `marimba` |
| `glocken` | 9 | Glockenspiel | `glockenspiel` / `bell` |

### lead（主旋律）

| 我们叫 | 号 | GM 名 | Logic 里搜什么 | 换的时候注意 |
|---|---:|---|---|---|
| `synth_lead` | 80 | Square Wave | `lead` / `synth lead` | 中性，通用 |
| `flute` | 73 | Flute | `flute` | 我们已加"每 2 小节呼吸" |
| `violin` | 40 | Violin | `violin` / `solo strings` | 需要连弓与揉弦，长音才像 |
| `sax` | 65 | Alto Sax | `sax` | 缺弯音，会偏"直" |
| `harmonica` | 22 | Harmonica | `harmonica` | 辨识度极高，容易露馅 |
| `whistle` | 78 | Whistle | `whistle` / `recorder` | 亲子 / 田园 |

### counter（副旋律）

| 我们叫 | 号 | GM 名 | Logic 里搜什么 |
|---|---:|---|---|
| `cello` | 42 | Cello | `cello` |
| `viola` | 41 | Viola | `viola` |
| `french_horn` | 60 | French Horns | `french horn` / `horn` |
| `bassoon` | 70 | Bassoon | `bassoon` |

> `counter_voice: "high"`（上方对位）时别用大提琴 / 巴松 —— 音区不对，会显得"尖"。

### pad（铺底）

| 我们叫 | 号 | GM 名 | Logic 里搜什么 |
|---|---:|---|---|
| `polysynth` | 90 | Polysynth | `pad` |
| `warm` | 89 | Warm Pad | `warm pad` / `analog pad` |
| `strings` | 48 | Strings | `strings` / `ensemble` |
| `choir` | 52 | Choir Aahs | `choir` / `vocal` |
| `church` | 19 | Church Org.1 | `organ` / `church` |

---

## 五、为什么做不到"自动对"

想让 MIDI 直接指定"加载 Studio Grand"，技术上不行：MIDI 文件里**没有**这个字段。
能带的信息只有 program 号、库号（bank MSB/LSB）、通道号 —— 而那些指的是 GM/GS/XG 的库，
不是 Logic 的 patch。

能做到的是两件替代方案：

1. **一份清单 + 一次手动对**（现在这份文档）：一次性，十分钟；
2. **模板工程**：对完之后存成模板，后面每首导入套用，就再也不用对了。

---

## 六、我想用你的真机数据补什么

现在这份表的"Logic 里搜什么"是按类别给的建议。要变成**实测映射**（导入后 Logic 实际给了哪条轨什么音色），
需要你在 Logic 里做一次导入并存成工程，我会解析出真实结果。

具体怎么给，见 [README.md](README.md) 的「需要你提供什么」一节。
