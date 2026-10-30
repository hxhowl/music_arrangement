---
name: logic-import
description: 把生成的 MIDI 导入 Logic Pro，做音色映射、试听验收与反馈收集
---

# logic-import

> **这个 skill 不由 AI 执行**：DAW 里的操作只能人做。
> AI 的职责是——给步骤、给核对清单、把人的反馈翻译成下一次要改哪一层。

## 导入前先跑体检
```bash
bash tools/check.sh projects/<dir>/music/output/<file>.mid projects/<dir>
```
体检已经把「空轨 / 段落没音 / 小节数不符 / PPQ 不对 / 鼓不在 channel 10」都拦掉了，
不要带着已知问题进 DAW，否则你会花时间在 Logic 里查一个代码 bug。

## 导入

- **新工程**：`File > Open` 直接打开 `.mid`，Logic 会按文件里的 BPM 与拍号建工程（推荐）
- **并入现有工程**：`File > Import > MIDI File…`，或把 `.mid` 拖到 Tracks 区
  ⚠️ 并入时不一定会改工程速度，先在文件里确认 BPM，再手动对齐或直接新建工程

文件的固定形态：Format 1 / PPQ 960 / 8 轨，鼓与打击乐落 channel 10。

## 音色

**先读 `references/logic-import.md`**：那里有逐槽的 program 号 → GM 音色名 → Logic 该搜什么，
数据是从本机导出的，不是猜的。**别凭印象报 patch 名** —— 音色库每台机器都不一样。

轨道自带的 GM program 来自 `config.json` 的 `preset` / `instruments`
（`bash tools/instruments.sh --project <dir>` 可以看这首歌实际用了什么）。
Logic 打开 MIDI 时会按它分配软件乐器；**最终都要按你的音源库调**：

| 轨 | GM 兜底 | 建议 |
|---|---|---|
| chords | 0 原声钢琴 | Alchemy（Pad 类）/ Piano |
| bass | 33 电贝斯（指弹） | Studio Bass / 合成贝斯 |
| drums | GM 鼓组 | Drum Machine Designer |
| perc | GM 打击乐 | 打击乐采样（沙锤/铃鼓/侧击） |
| arp | 81 Lead 2 | Pluck / Alchemy 琶音 |
| lead | 80 方波主音 | Alchemy / ES2 |
| counter | 42 大提琴 | 大提琴 / 圆号 / 低音木管（**要比 lead 暗**，否则抢主旋律） |
| pad | 90 Pad | Sculpture / Strings |

换音色属于演奏层，不需要回改代码。

`counter` 如果全程没音，不是 bug：它只在主旋律空档出声，副歌旋律铺满时自然不会出现。

## 验收检查表

按顺序过一遍，任何一条不过就先别继续精修（判断标准以该项目的 `brief.md` 为准）：

- [ ] 8 轨都在，没有空白轨（`counter` 允许空，见上）
- [ ] 和弦变化频率对得上 `config.json` 的 `harmonic_rhythm`（2 = 半小节就换）
- [ ] 如果 `swing` 不为 0，鼓和贝斯的反拍应当同时"拖"一点，不是只有某一轨
- [ ] BPM、拍号与 `brief.md` 一致
- [ ] 和弦听起来与 `brief.md` 写的进行一致（例：F#m-D-A-E）
- [ ] 段落边界与 `brief.md` 的音轨规划一致
      （默认编排：intro/outro 只有和弦+pad；副歌起点有吊镲；
      只有 full 密度的段落才每 4 小节有过门，半拍的段落没有）
- [ ] 副歌比主歌"起来"了（密度、力度、轨道数）
- [ ] 留白够（cinematic 的鼓应该只有心跳，不该是满编）
- [ ] 鼓键位正确（底鼓/军鼓/踩镲没串到别的音色上）
- [ ] 没有明显音域不合适的音（贝斯跑到中频、pad 挤压人声频段）

## 输出

给用户一段可以直接照着做的结论：

1. 这版**能不能用**（能用 / 修完再用 / 重写）
2. 具体问题清单，每条按「**段落 + 乐器 + 现象**」写，并标注该改哪一层
   —— 例如“副歌的贝斯太密，跟底鼓打架” → `music/core/styles.py` 的 `bass.rhythm`
3. 建议的下一步（回 `midi-iterate` 改哪一层 / 直接进 Logic 精修）

## 音效轨（cues）

`<name>-vN.cues.md` 里是 riser / impact / whoosh 的时间点，**不在 MIDI 里**：

1. 新建一条**音频轨**，命名 `SFX`
2. 按「小节.拍」摆采样（不要按秒 —— 改 BPM 时秒数会变，小节不会）
3. impact 的 sub 部分建议高通到 40Hz 以上，别和底鼓抢

## 试听

- 先 `File > Bounce > Section`（划出 30s cycle 区）导一段，比整首来回拉更省时间
- 导出设置按项目约定：48kHz / 24bit

## 边界
不做离线合成、不做自动混音评估 —— 好不好听由人判断，代码只保证结构和和声正确。
