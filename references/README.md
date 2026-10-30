# references —— 本机真机数据导出的参考表

这个目录回答一个问题：**MIDI 里的 program 号，在你自己的 Logic 里到底对应什么。**

| 文件 | 内容 | 谁维护 |
|---|---|---|
| [gm-programs.md](gm-programs.md) | 128 个 GM 音色 + 9 个鼓组的**本机实际名字**，以及我们哪个槽用了哪个号 | 自动生成 |
| [logic-patches.md](logic-patches.md) | Logic 音色库的规模与分类，以及每个槽该搜什么关键词 | 自动生成 |
| [logic-import.md](logic-import.md) | 导入 Logic 后逐槽怎么对音色（手写的对照参考） | 手写 |
| `source/` | 你放**真机导入工程**的地方（不进 git） | 你 |

---

## 数据从哪来

都不是凭记忆写的，全部读自本机文件：

| 数据 | 来源 |
|---|---|
| GM 音色名 | `/System/Library/Components/CoreAudio.component/Contents/Resources/gs_instruments.dls` |
| 鼓组名 | 同一个文件里的 `bank 0x80000000`（通道 10 用的就是这套） |
| Logic patch 清单 | `Logic Pro.app/.../Library.bundle/Patches/Instrument` 与 `~/Music/Logic Pro Library.bundle/Patches/Instrument` |
| Logic 版本 | `Logic Pro.app/Contents/Info.plist` |

## 怎么重新生成

```bash
python tools/gen_references.py            # 重新生成两份自动表
python tools/gen_references.py --list-dls # 只打印 GM 解析结果，不写文件
```

什么时候该重跑：

- Logic 升级、或新装了音色库（patch 数量会变）；
- 换了电脑（路径不同，脚本会自己报告"未找到"）；
- 改了 `music/core/instruments.py` 里的 program 号（"我们用到的"那一列会跟着变）。

---

## 需要你提供什么（这是唯一需要你动手的一步）

自动表能告诉我 **"我们发了什么号"** 和 **"你机器上有哪些音色"**，
但只有 Logic 真跑一遍，才知道 **"它给了哪条轨什么音色"** —— 也就是你觉得"对不上"的那个结果。

### 最有用：一次导入的原始工程（约 2 分钟）

1. Logic 里 `文件 > 新建`，选**空白工程**（不要用模板，否则看到的不是导入行为）；
2. 把 `projects/demo/music/output/demo-v9.mid` 直接拖进去（或 `文件 > 打开` 选它）；
3. **什么都别改**，直接 `文件 > 存储`；
4. 存成：

   ```
   references/source/import-demo.logicx
   ```

5. 跟我说一声"放好了"，我来解析。

我会从工程里读：轨道数、每条轨的名字、每条轨实际加载的乐器 / 采样器音色
（`MetaData.plist` 里有 `NumberOfTracks` 与 `SamplerInstrumentsFiles`，
`ProjectData` 里能取到轨道名与乐器引用）。**只读结构，不碰 `Media/` 里的音频。**

### 可选，但很加分

- **对完之后的样子**：如果你手工把音色换对了，再存一份 `references/source/import-demo-mapped.logicx`。
  两份一对比，就能得出"Logic 自动给的 → 你实际想要的"，这才是真正可用的映射表。
- **第三方音源**：如果你常用 Kontakt / Omnisphere 之类，告诉我名字（或 `ls ~/Library/Audio/Presets` 的结果），
  我把它们也列进候选，不然我只能推荐 Logic 自带的。

### 不用给的东西

- 截图（信息量远不如工程文件，而且我要抄半天）
- 音频 bounce（跟"乐器对应"没关系）
- 整首编曲工程（除非你想让我看某一版的真实配器）

> `references/source/` 已经在 `.gitignore` 里，你的工程不会被提交进仓库。
