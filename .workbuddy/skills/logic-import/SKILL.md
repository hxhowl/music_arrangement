---
name: logic-import
description: 把生成的 MIDI 导入 Logic Pro，做音色映射、试听验收与反馈收集
---

# logic-import

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

文件的固定形态：Format 1 / PPQ 960 / 5 轨，鼓轨落 channel 10。

## 音色

轨道自带 GM program 兜底（Logic 会按它分配软件乐器），**都要换掉**：

| 轨 | GM 兜底 | 建议 |
|---|---|---|
| chords | 0 原声钢琴 | Alchemy（Pad 类）/ Piano |
| bass | 33 电贝斯（指弹） | Studio Bass / 合成贝斯 |
| drums | GM 鼓组 | Drum Machine Designer |
| lead | 80 方波主音 | Alchemy / ES2 |
| pad | 90 Pad | Sculpture / Strings |

换音色属于演奏层，不需要回改代码。

## 验收检查表

按顺序过一遍，任何一条不过就先别继续精修：

- [ ] 5 轨都在，没有空白轨
- [ ] BPM、拍号与 `brief.md` 一致
- [ ] 和弦听起来与 `brief.md` 写的进行一致（例：F#m-D-A-E）
- [ ] 段落边界对得上：intro 无鼓、副歌起点有吊镲、每 4 小节有过门
- [ ] 副歌比主歌"起来"了（密度、力度、轨道数）
- [ ] 留白够（尤其 cinematic：鼓应该只有心跳，不该是满编）
- [ ] 鼓键位正确（底鼓/军鼓/踩镲没串到别的音色上）
- [ ] 没有明显音域不合适的音（贝斯跑到中频、pad 挤压人声频段）

## 试听与反馈

- 先 `File > Bounce > Section`（划出 30s cycle 区）导一段，比整首来回拉更省时间
- 导出设置按项目约定：48kHz / 24bit
- 反馈请按「**哪一段 + 哪个乐器 + 什么问题**」说，例如：
  “副歌的贝斯太密，跟底鼓打架”“前奏 pad 太亮，抢戏”
  这类话可以直接进 `midi-iterate` 定位到 `music/core/styles.py` 的哪一段参数

## 边界
不做离线合成、不做自动混音评估 —— 好不好听由人判断，代码只保证结构和和声正确。
