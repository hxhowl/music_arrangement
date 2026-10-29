---
name: midi-iterate
description: 用户对已生成版本有意见时（鼓太弱、太吵、想更空、太快太慢、没记忆点），只改当前这首歌的 config 再重新生成
---

# midi-iterate

## 铁律：改动只作用于当前这首歌

**所有调整都改 `projects/<dir>/config.json`。不要改 `music/core/` 下的任何文件。**

原因：`music/core/arrange.py` 和 `music/core/styles.py` 是**出厂默认库**，
改了会影响所有引用它的项目，历史版本再也生成不出来 —— 这正是之前花了三轮才修掉的病。

项目要的个性化，`config.json` 里都有对应开关（见下表）。改完旧版本不受影响，
因为每版都有 `-vN.config.json` 快照。

## 流程
1. 读 `projects/<dir>/config.json` 与 `decisions.md`
2. 按下表定位到**一个** config 字段
3. 改它 → `bash tools/compose.sh projects/<dir>`（版本自增 + 体检）
4. 在 `decisions.md` 追加：改了什么 / 为什么 / 预期听感变化
5. 输出：改了哪个字段 + 体检结论 + 新版本号 + "和上一版比应该听到什么差别"

## 反馈 → config 字段

| 用户说 | 改 `config.json` 的 | 说明 |
|--------|---------------------|------|
| 太快 / 太慢 | `bpm` | |
| 换个调 | `key` | 和弦会跟着变，不用改和弦名 |
| 换和弦进行 | `progression` | 级数写法，如 `["i","VI","III","VII"]` |
| 整体气质不对（太摇滚 / 想更空） | `style` | 整套换掉（影响全曲） |
| 只有某一段想要另一种感觉 | `arrange.<段>.style` | 例如副歌 pop、结尾 playful |
| 某一轨太吵 / 太弱 | `style_tweaks.<轨>.velocity` | chords / bass / pad / lead |
| 鼓太密 / 太稀 | `arrange.<段>.drums` | `None` / `light` / `medium` / `full` |
| 鼓的花活不对 | `style_tweaks.drums.<档>` | 换掉某一档的谱型 |
| 过门太频繁 | `style_tweaks.fill_every` | 每 N 小节一次 |
| 不想要吊镲 | `arrange.<段>.crash` | `true` / `false` |
| 贝斯太密 / 走向奇怪 | `style_tweaks.bass.rhythm` | 节奏型，可改切分 |
| 旋律太满 / 太空 | `style_tweaks.lead.breath_every` | 每 N 小节呼吸一次，0 = 不呼吸 |
| 副歌没起来 | `arrange.chorus` 的 `vel` 或 `drums` | 只动副歌 |
| 段落长度 / 想加 bridge | `sections` | 键名要在 `ARRANGE` 里存在 |
| 想多几版挑一个 | `seed` 或 `--takes N` | 见下 |

⚠️ `style_tweaks` 对**所有段落**生效（包括换了风格的段落）——它调的是"这首歌的演奏参数"，
不是"某个风格的定义"。要区分段落请用 `arrange.<段>`。

## 常用改法

```jsonc
{
  // 副歌再推一把，但鼓别太满
  "arrange": { "chorus": { "drums": "medium", "vel": 1.05 } },

  // 贝斯轻一点、旋律别每两小节就喘
  "style_tweaks": {
    "bass": { "velocity": 78 },
    "lead": { "breath_every": 8 }
  }
}
```

改完的值会进 `config.json`，也会进这一版的 `-vN.config.json` 快照。

## 多版本 / 换演奏

- `bash tools/compose.sh <dir> v5 --takes 3` → 出 v5/v6/v7，
  seed 从 config 的 `seed` 起递增（默认 0 → 1/2/3），
  是同一编曲的三种演奏（力度、鼓的装饰音、旋律短语起点不同）
- `bash tools/compose.sh <dir> --seed 9` → 换一个 seed 出一版。
  ⚠️ `--seed` 只影响这一版，会写进 `-vN.config.json` 快照，**不改 `config.json`**；
  想让某个 seed 成为该项目的默认，就手改 config 里的 `seed`
- seed 只改"演奏细节"，**不改和弦、段落、风格**。所以是同一首曲子的不同 take
- `seed: 0` 是默认值：完全确定，同参数两次生成字节相同

## 什么时候才允许改代码

只有当需要**新能力**时才动 `music/core/`，而且必须先说明"这是全局能力，不是这一首的调整"：

- 加一套全新风格 → `music/core/styles.py` 加条目（不影响已有项目，只是多一个可选值）
- 加一种新段落类型 → `music/core/arrange.py` 加 `ARRANGE` 条目
- 加一种新的和声手法 / 织体写法 → 新 pattern 或新字段

这类改动属于"扩产线"，不是"调这首歌"。做完要在 `decisions.md` 或 commit message 里写清影响面。

## 纪律
- 不改用户已在 Logic 里手调的自动化（那些只存在于工程文件里）
- 每次只迭代 1~2 个音乐问题，改多了听不出因果
- 体检不通过不许当作完成；不覆盖旧版（`tools/compose.sh` 已默认自增）
