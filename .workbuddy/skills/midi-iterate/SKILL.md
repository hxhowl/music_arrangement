---
name: midi-iterate
description: 根据 Logic 预览反馈，只改对应的那一层再重新生成，不手动改二进制
---

# midi-iterate

## 触发
用户回传预览意见：“鼓太弱 / 贝斯过密 / 副歌没记忆点 / 太摇滚了 / 想更空”。

## 流程
1. 读项目 `config.json`、`decisions.md`，以及上一版 `<name>-vN.config.json` 快照
2. 按下表判断该改哪一层，**只改那一层**
3. `bash tools/compose.sh projects/<dir>`（版本自增 + 自动体检）
4. 在 `decisions.md` 追加一条：改了什么 / 为什么 / 预期听感变化
5. 输出：改了哪一行 + 体检结论 + 新版本号 + 一句"和上一版比应该听到什么差别"

## 该改哪一层

| 用户说 | 改哪里 | 影响范围 |
|--------|--------|----------|
| 太快 / 太慢 / 换调 | `config.json` 的 `bpm` / `key` | 仅这首 |
| 换和弦进行 | `config.json` 的 `progression`（级数） | 仅这首 |
| 整体气质不对（太摇滚 / 想更空） | `config.json` 的 `style` | 仅这首 |
| 段落长度不对 / 想加 bridge | `config.json` 的 `sections` | 仅这首 |
| 副歌没起来 / 前奏太满 | `music/core/arrange.py` 的 `ARRANGE` | ⚠️ 所有项目 |
| 鼓太弱 / 太吵 / 要过门 | `music/core/styles.py` 对应风格的 `drums` | ⚠️ 同风格所有项目 |
| 贝斯过密 / 走向奇怪 | `music/core/styles.py` 对应风格的 `bass` | ⚠️ 同风格所有项目 |
| 旋律没记忆点 | `music/core/styles.py` 对应风格的 `lead` | ⚠️ 同风格所有项目 |

### 只想改一首歌怎么办

- 参数类（bpm/key/progression/sections）：直接改 `config.json`，天然只影响这一首
- 演奏类（鼓/贝斯/旋律）：**复制一份风格条目**再切 `style`，不要原地改。
  先在 `music/core/styles.py` 复制 `"pop"` 改名为 `"pop_dark"` 并调参数，
  再把 `config.json` 的 `style` 改成 `pop_dark`
- 编排类（哪段进鼓）：`ARRANGE` 目前**没有** per-project 覆盖，改了就是全局。
  已生成的旧 mid 不受影响，但旧项目重新生成会跟着变。
  真要只改一首，就在 `config.json` 的 `sections` 里调整长度来间接达到——
  或者先提出来加 per-project 覆盖（这是已知缺口）。

## 纪律
- 不改用户已在 Logic 里手调的自动化（那些只存在于工程文件里，不在本仓库）
- 每次只迭代 1~2 个音乐问题，改多了听不出因果
- 改全局文件前先 `git status` 确认工作区干净，便于事后对照或回滚
- 体检不通过不许当作完成；不覆盖旧版（`tools/compose.sh` 已默认自增）
