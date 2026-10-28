# demo

> 工程验证用的样例项目：检验链路跑得通、体检能抓到问题、换风格/换调真的会变。

## 参数

| 项 | 值 |
|---|---|
| 风格 | `cinematic` |
| 调性 | `F#m` |
| 和弦进行 | F#m - D - A - E |
| BPM | 84 |
| 时长 | 约 69 秒（24 小节，2.86 秒/小节） |

## 段落

| 段落 | 小节 | 起始小节 |
|---|---|---|
| intro | 4 | 第 1 小节 |
| verse | 8 | 第 5 小节 |
| chorus | 8 | 第 13 小节 |
| outro | 4 | 第 21 小节 |

## 音轨规划

由 `music/core/arrange.py` 的 `ARRANGE` 决定，风格决定每档具体怎么打。

| 段落 | chords | bass | drums | lead | pad | 力度 |
|---|---|---|---|---|---|---|
| intro | ✓ | — | — | — | ✓ | 0.70 |
| verse | ✓ | ✓ | medium | — | ✓ | 0.85 |
| chorus | ✓ | ✓ | full | ✓ | ✓ | 1.00 |
| outro | ✓ | — | — | — | ✓ | 0.65 |

## 下一步

```bash
bash tools/compose.sh projects/demo
```

然后把 `music/output/demo-v5.mid` 拖进 Logic Pro，换音色、调力度、加自动化。
改动理由写进同目录的 `decisions.md`。

## 必须真人完成的部分

- 人声（本链路不生成人声）
- 音色与混音决策
- 最终成品是否可用
