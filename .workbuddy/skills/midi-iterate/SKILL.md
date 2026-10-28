---
name: midi-iterate
description: 根据 Logic 预览反馈，只改对应的那一层再重新生成，不手动改二进制
---

# midi-iterate

## 触发
用户回传 preview 问题：“鼓太弱 / 贝斯过密 / 副歌没记忆点 / 太摇滚了”。

## 流程
1. 读项目 `config.json`、`decisions.md`，以及上一版 `<name>-vN.config.json` 快照
2. 按下表判断该改哪一层，**只改那一层**
3. `bash tools/compose.sh projects/<dir>`（版本号自增 + 自动体检）
4. 在 `decisions.md` 追加一条：改了什么 / 为什么 / 预期听感变化
5. 输出：diff 说明 + 体检结论 + 新版本号

## 该改哪一层

| 用户说 | 改哪里 | 影响范围 |
|--------|--------|----------|
| 太快 / 太慢 / 换调 | 项目 `config.json` 的 `bpm` / `key` | 仅这首 |
| 换和弦进行 | `config.json` 的 `progression`（级数） | 仅这首 |
| 整体气质不对（太摇滚 / 想更空） | `config.json` 的 `style` | 仅这首 |
| 副歌没起来 / 前奏太满 / 想加段落 | `music/core/arrange.py` 的 `ARRANGE` | 所有项目 |
| 鼓太弱 / 太吵 / 要过门 | `music/core/styles.py` 对应风格的 `drums` | 同风格所有项目 |
| 贝斯过密 / 走向奇怪 | `music/core/styles.py` 对应风格的 `bass` | 同风格所有项目 |
| 旋律没记忆点 | `music/core/styles.py` 对应风格的 `lead` | 同风格所有项目 |

**只改一首歌的律动**：复制一份风格条目（如 `"pop_dark": {...}`）再切 `config.json` 的 `style`，
不要原地改 `pop`，否则同风格的历史项目全部变样。

## 纪律
- 不改用户已在 Logic 里手调的自动化
- 每次只迭代 1~2 个音乐问题
- 体检不通过不许当作完成
- 不覆盖旧版（compose.sh 已默认自增版本号）
