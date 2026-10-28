---
name: midi-iterate
description: 根据 Logic 预览反馈，只改代码重新生成 MIDI，不手动改二进制
---

# midi-iterate

## 触发
用户回传 preview 问题：“鼓太弱 / 贝斯过密 / 副歌没记忆点”。

## 流程
1. 读项目 `decisions.md`、`config.json`，以及上一版的 `<name>-vN.config.json` 快照
2. 判断问题该改哪一层（见下表），只改那一层
3. 跑 `bash tools/compose.sh projects/<dir>`（版本号自动 +1，自动体检）
4. 在 `decisions.md` 追加一条：改了什么 / 为什么 / 预期听感变化
5. 输出 diff 说明 + 体检结论

## 该改哪一层

| 用户说 | 改哪里 |
|--------|--------|
| 太快 / 太慢 / 想换个调 / 段落长度不对 | 项目 `config.json` |
| 副歌没起来 / 前奏太满 / 想要留白 | `music/core/arrange.py` 的 `ARRANGE` |
| 鼓太弱 / 太吵 / 想要过门 | `patterns/drums.py`（密度档位与过门） |
| 贝斯过密 / 走向奇怪 | `patterns/bass.py` |
| 和弦不对 / 想换进行 | `music/core/theory.py` + `patterns/chords.py` |
| 旋律没记忆点 / 和和弦打架 | `patterns/lead.py` |

## 纪律
- 不改用户已在 Logic 里手调的自动化
- 每次只迭代 1~2 个音乐问题
- 体检不通过不许当作完成
- 不覆盖旧版（compose.sh 已默认自增版本号）
