# GM 音色对照表（本机导出）

> 自动生成，别手改 —— 重新跑 `python tools/gen_references.py`。

- 数据来源：`/System/Library/Components/CoreAudio.component/Contents/Resources/gs_instruments.dls`
- 这 128 个名字就是 macOS 自带 GM 音色库里的**实际名字**。
  Logic 打开 `.mid` 时按 program 号取的就是这套音色（不是 Logic 音色库）。
- 生成时间：2026-10-31　Logic 版本：12.2 (6644)

「我们用到的」指 `music/core/instruments.py` 里哪些乐器选项写的就是这个号。
鼓组号（`drums` / `perc`）和旋律音色的号会重复，所以单独标「鼓组」——
它们在同一条 MIDI 通道上含义不同：通道 10 的 program 选的是**鼓组**。

| 号 | 族 | 本机音色名 | 我们用到的 |
|---:|---|---|---|
| 0 | 钢琴 | Piano 1 | `chords.piano`、`drums.standard`（鼓组） |
| 1 | 钢琴 | Piano 2 |  |
| 2 | 钢琴 | Piano 3 |  |
| 3 | 钢琴 | Honky-tonk |  |
| 4 | 钢琴 | E.Piano 1 | `chords.epiano` |
| 5 | 钢琴 | E.Piano 2 |  |
| 6 | 钢琴 | Harpsichord |  |
| 7 | 钢琴 | Clav. |  |
| 8 | 色彩打击 | Celesta | `drums.room`（鼓组） |
| 9 | 色彩打击 | Glockenspiel | `arp.glocken` |
| 10 | 色彩打击 | Music Box |  |
| 11 | 色彩打击 | Vibraphone |  |
| 12 | 色彩打击 | Marimba | `arp.marimba` |
| 13 | 色彩打击 | Xylophone |  |
| 14 | 色彩打击 | Tubular-bell |  |
| 15 | 色彩打击 | Santur |  |
| 16 | 风琴 | Organ 1 | `chords.organ`、`drums.power`（鼓组） |
| 17 | 风琴 | Organ 2 |  |
| 18 | 风琴 | Organ 3 |  |
| 19 | 风琴 | Church Org.1 | `pad.church` |
| 20 | 风琴 | Reed Organ |  |
| 21 | 风琴 | Accordion Fr |  |
| 22 | 风琴 | Harmonica | `lead.harmonica` |
| 23 | 风琴 | Bandoneon |  |
| 24 | 吉他 | Nylon-str.Gt | `chords.nylon`、`drums.electronic`（鼓组） |
| 25 | 吉他 | Steel-str.Gt | `chords.steel` |
| 26 | 吉他 | Jazz Gt. |  |
| 27 | 吉他 | Clean Gt. |  |
| 28 | 吉他 | Muted Gt. |  |
| 29 | 吉他 | Overdrive Gt |  |
| 30 | 吉他 | DistortionGt |  |
| 31 | 吉他 | Gt.Harmonics |  |
| 32 | 贝斯 | Acoustic Bs. | `bass.upright` |
| 33 | 贝斯 | Fingered Bs. | `bass.finger` |
| 34 | 贝斯 | Picked Bs. | `bass.pick` |
| 35 | 贝斯 | Fretless Bs. |  |
| 36 | 贝斯 | Slap Bass 1 |  |
| 37 | 贝斯 | Slap Bass 2 |  |
| 38 | 贝斯 | Synth Bass 1 | `bass.synth` |
| 39 | 贝斯 | Synth Bass 2 |  |
| 40 | 弦乐 | Violin | `drums.brush`（鼓组）、`lead.violin` |
| 41 | 弦乐 | Viola | `counter.viola` |
| 42 | 弦乐 | Cello | `counter.cello` |
| 43 | 弦乐 | Contrabass |  |
| 44 | 弦乐 | Tremolo Str |  |
| 45 | 弦乐 | PizzicatoStr | `arp.pluck` |
| 46 | 弦乐 | Harp | `arp.harp` |
| 47 | 弦乐 | Timpani |  |
| 48 | 合奏 | Strings | `chords.strings`、`pad.strings` |
| 49 | 合奏 | Slow Strings |  |
| 50 | 合奏 | Syn.Strings1 |  |
| 51 | 合奏 | Syn.Strings2 |  |
| 52 | 合奏 | Choir Aahs | `pad.choir` |
| 53 | 合奏 | Voice Oohs |  |
| 54 | 合奏 | SynVox |  |
| 55 | 合奏 | OrchestraHit |  |
| 56 | 铜管 | Trumpet |  |
| 57 | 铜管 | Trombone |  |
| 58 | 铜管 | Tuba |  |
| 59 | 铜管 | MutedTrumpet |  |
| 60 | 铜管 | French Horns | `counter.french_horn` |
| 61 | 铜管 | Brass 1 |  |
| 62 | 铜管 | Synth Brass1 |  |
| 63 | 铜管 | Synth Brass2 |  |
| 64 | 簧管 | Soprano Sax |  |
| 65 | 簧管 | Alto Sax | `lead.sax` |
| 66 | 簧管 | Tenor Sax |  |
| 67 | 簧管 | Baritone Sax |  |
| 68 | 簧管 | Oboe |  |
| 69 | 簧管 | English Horn |  |
| 70 | 簧管 | Bassoon | `counter.bassoon` |
| 71 | 簧管 | Clarinet |  |
| 72 | 管乐 | Piccolo |  |
| 73 | 管乐 | Flute | `lead.flute` |
| 74 | 管乐 | Recorder |  |
| 75 | 管乐 | Pan Flute |  |
| 76 | 管乐 | Bottle Blow |  |
| 77 | 管乐 | Shakuhachi |  |
| 78 | 管乐 | Whistle | `lead.whistle` |
| 79 | 管乐 | Ocarina |  |
| 80 | 合成主音 | Square Wave | `lead.synth_lead` |
| 81 | 合成主音 | Saw Wave | `arp.synth` |
| 82 | 合成主音 | Syn.Calliope |  |
| 83 | 合成主音 | Chiffer Lead |  |
| 84 | 合成主音 | Charang |  |
| 85 | 合成主音 | Solo Vox |  |
| 86 | 合成主音 | 5th Saw Wave |  |
| 87 | 合成主音 | Bass & Lead |  |
| 88 | 合成铺底 | Fantasia |  |
| 89 | 合成铺底 | Warm Pad | `pad.warm` |
| 90 | 合成铺底 | Polysynth | `pad.polysynth` |
| 91 | 合成铺底 | Space Voice |  |
| 92 | 合成铺底 | Bowed Glass |  |
| 93 | 合成铺底 | Metal Pad |  |
| 94 | 合成铺底 | Halo Pad |  |
| 95 | 合成铺底 | Sweep Pad |  |
| 96 | 合成效果 | Ice Rain |  |
| 97 | 合成效果 | Soundtrack |  |
| 98 | 合成效果 | Crystal |  |
| 99 | 合成效果 | Atmosphere |  |
| 100 | 合成效果 | Brightness |  |
| 101 | 合成效果 | Goblin |  |
| 102 | 合成效果 | Echo Drops |  |
| 103 | 合成效果 | Star Theme |  |
| 104 | 民族乐器 | Sitar |  |
| 105 | 民族乐器 | Banjo |  |
| 106 | 民族乐器 | Shamisen |  |
| 107 | 民族乐器 | Koto |  |
| 108 | 民族乐器 | Kalimba |  |
| 109 | 民族乐器 | Bagpipe |  |
| 110 | 民族乐器 | Fiddle |  |
| 111 | 民族乐器 | Shanai |  |
| 112 | 打击乐 | Tinkle Bell |  |
| 113 | 打击乐 | Agogo |  |
| 114 | 打击乐 | Steel Drums |  |
| 115 | 打击乐 | Woodblock |  |
| 116 | 打击乐 | Taiko |  |
| 117 | 打击乐 | Melo. Tom 1 |  |
| 118 | 打击乐 | Synth Drum |  |
| 119 | 打击乐 | Reverse Cym. |  |
| 120 | 音效 | Gt.FretNoise |  |
| 121 | 音效 | Breath Noise |  |
| 122 | 音效 | Seashore |  |
| 123 | 音效 | Bird |  |
| 124 | 音效 | Telephone 1 |  |
| 125 | 音效 | Helicopter |  |
| 126 | 音效 | Applause |  |
| 127 | 音效 | Gun Shot |  |

## 我们实际用到的号（逐槽展开）

| 槽 | 乐器 | program | 本机音色名 |
|---|---|---:|---|
| `chords` | `piano` | 0 | Piano 1 |
| `chords` | `epiano` | 4 | E.Piano 1 |
| `chords` | `nylon` | 24 | Nylon-str.Gt |
| `chords` | `steel` | 25 | Steel-str.Gt |
| `chords` | `strings` | 48 | Strings |
| `chords` | `organ` | 16 | Organ 1 |
| `bass` | `finger` | 33 | Fingered Bs. |
| `bass` | `pick` | 34 | Picked Bs. |
| `bass` | `upright` | 32 | Acoustic Bs. |
| `bass` | `synth` | 38 | Synth Bass 1 |
| `drums` | `standard` | 0 | `Standard`（本槽决定鼓组） |
| `drums` | `room` | 8 | `Room`（本槽决定鼓组） |
| `drums` | `power` | 16 | `Power`（本槽决定鼓组） |
| `drums` | `electronic` | 24 | `Electronic`（本槽决定鼓组） |
| `drums` | `brush` | 40 | `Brush`（本槽决定鼓组） |
| `perc` | `shaker` | — | 跟随 `drums` 的鼓组 |
| `perc` | `tambourine` | — | 跟随 `drums` 的鼓组 |
| `perc` | `rim` | — | 跟随 `drums` 的鼓组 |
| `perc` | `congas` | — | 跟随 `drums` 的鼓组 |
| `perc` | `clap` | — | 跟随 `drums` 的鼓组 |
| `arp` | `pluck` | 45 | PizzicatoStr |
| `arp` | `harp` | 46 | Harp |
| `arp` | `marimba` | 12 | Marimba |
| `arp` | `synth` | 81 | Saw Wave |
| `arp` | `glocken` | 9 | Glockenspiel |
| `lead` | `synth_lead` | 80 | Square Wave |
| `lead` | `flute` | 73 | Flute |
| `lead` | `violin` | 40 | Violin |
| `lead` | `sax` | 65 | Alto Sax |
| `lead` | `harmonica` | 22 | Harmonica |
| `lead` | `whistle` | 78 | Whistle |
| `counter` | `cello` | 42 | Cello |
| `counter` | `viola` | 41 | Viola |
| `counter` | `french_horn` | 60 | French Horns |
| `counter` | `bassoon` | 70 | Bassoon |
| `pad` | `polysynth` | 90 | Polysynth |
| `pad` | `warm` | 89 | Warm Pad |
| `pad` | `strings` | 48 | Strings |
| `pad` | `choir` | 52 | Choir Aahs |
| `pad` | `church` | 19 | Church Org.1 |

## 鼓组号（通道 10，和上面的旋律音色是两套）

`drums` 与 `perc` 都落在 MIDI 通道 10。**同一个号在这条通道上是鼓组，
在别的通道上是旋律音色** —— 这就是为什么 0 号既叫 “Piano 1” 又叫 “Standard”。

| program | 本机鼓组名 | 我们用到的 |
|---:|---|---|
| 0 | Standard | `drums.standard` |
| 8 | Room | `drums.room` |
| 16 | Power | `drums.power` |
| 24 | Electronic | `drums.electronic` |
| 25 | TR-808 |  |
| 32 | Jazz |  |
| 40 | Brush | `drums.brush` |
| 48 | Orchestra |  |
| 56 | SFX |  |

## 编制预设用到的号

- **band**：`chords`=电钢琴（4 → E.Piano 1）；`bass`=指弹电贝斯（33 → Fingered Bs.）；`drums`=标准鼓组（0 → Piano 1）；`perc`=铃鼓（鼓组随 `drums`）；`arp`=拨弦（pizzicato）（45 → PizzicatoStr）；`lead`=方波主音（80 → Square Wave）；`counter`=大提琴（42 → Cello）；`pad`=暖 Pad（89 → Warm Pad）
- **cinematic**：`chords`=弦乐群（48 → Strings）；`bass`=立式贝斯（32 → Acoustic Bs.）；`drums`=Room 鼓组（8 → Celesta）；`perc`=沙锤（鼓组随 `drums`）；`arp`=竖琴（46 → Harp）；`lead`=小提琴（40 → Violin）；`counter`=圆号（60 → French Horns）；`pad`=弦乐群（48 → Strings）
- **lofi**：`chords`=电钢琴（4 → E.Piano 1）；`bass`=立式贝斯（32 → Acoustic Bs.）；`drums`=刷子鼓组（40 → Violin）；`perc`=沙锤（鼓组随 `drums`）；`arp`=马林巴（12 → Marimba）；`lead`=长笛（73 → Flute）；`counter`=大提琴（42 → Cello）；`pad`=暖 Pad（89 → Warm Pad）
- **acoustic**：`chords`=尼龙弦吉他（24 → Nylon-str.Gt）；`bass`=立式贝斯（32 → Acoustic Bs.）；`drums`=刷子鼓组（40 → Violin）；`perc`=康加鼓（鼓组随 `drums`）；`arp`=竖琴（46 → Harp）；`lead`=长笛（73 → Flute）；`counter`=大提琴（42 → Cello）；`pad`=弦乐群（48 → Strings）
- **electronic**：`chords`=电钢琴（4 → E.Piano 1）；`bass`=合成贝斯（38 → Synth Bass 1）；`drums`=电子鼓组（24 → Nylon-str.Gt）；`perc`=拍手（鼓组随 `drums`）；`arp`=合成琶音（81 → Saw Wave）；`lead`=方波主音（80 → Square Wave）；`counter`=大提琴（42 → Cello）；`pad`=合成铺底（90 → Polysynth）
