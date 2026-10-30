#!/usr/bin/env python3
"""从**本机**导出参考表到 references/。

数据来源都是真机文件，不是凭记忆写的：

  1. `/System/Library/.../CoreAudio.component/Contents/Resources/gs_instruments.dls`
     —— macOS 自带的 GM 音色库。Logic 打开 .mid 时按 program 号取的就是这套音色，
        这里把 128 个 program 的**实际名字**解析出来。
  2. Logic 的 patch 库（Library 面板里能点到的音色），两个根：
       - `/Applications/Logic Pro.app/.../Library.bundle/Patches/Instrument`
       - `~/Music/Logic Pro Library.bundle/Patches/Instrument`（下载的完整音色库）

用法:
    python tools/gen_references.py              # 重新生成（Logic 升级/装新音色后跑一次）
    python tools/gen_references.py --list-dls   # 只打印 GM 解析结果，不写文件

这个脚本只读系统文件，不碰你的 Logic 工程，也不会启动 Logic。
"""

import argparse
import datetime
import os
import plistlib
import struct
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_MUSIC = os.path.join(_ROOT, "music")
if _MUSIC not in sys.path:
    sys.path.insert(0, _MUSIC)

from core.instruments import INSTRUMENTS, KIT_SHARED, PRESETS  # noqa: E402

DLS_PATH = (
    "/System/Library/Components/CoreAudio.component/Contents/Resources/gs_instruments.dls"
)
PATCH_ROOTS = (
    "/Applications/Logic Pro.app/Contents/Resources/Library.bundle/Patches/Instrument",
    os.path.expanduser("~/Music/Logic Pro Library.bundle/Patches/Instrument"),
)
OUT_DIR = os.path.join(_ROOT, "references")
WALK_DEPTH = 4          # patch 包最深 4 层就够，再深只是包内部结构

# GM 的 16 个族，每族 8 个音色
GM_FAMILIES = (
    "钢琴", "色彩打击", "风琴", "吉他", "贝斯", "弦乐", "合奏", "铜管",
    "簧管", "管乐", "合成主音", "合成铺底", "合成效果", "民族乐器", "打击乐", "音效",
)

# 每个槽在 Logic 库里找音色时该用的关键词（用来从几千个 patch 里筛候选）
SLOT_KEYWORDS = {
    "chords": ("piano", "grand", "upright", "felt", "rhodes", "wurli", "guitar",
               "nylon", "steel", "strings", "ensemble", "organ"),
    "bass": ("bass",),
    "drums": ("kit",),
    "perc": ("percussion", "shaker", "tambourine", "conga", "clap"),
    "arp": ("arp", "pluck", "harp", "marimba", "bell", "glocken"),
    "lead": ("lead", "flute", "violin", "sax", "harmonica", "whistle"),
    "counter": ("cello", "viola", "horn", "bassoon", "string"),
    "pad": ("pad", "strings", "choir", "vocal", "organ"),
}


# ---------------------------------------------------------------- DLS 解析


def _chunks(buf, start, end):
    """遍历 RIFF 块。返回 (id, body_start, body_end)。"""
    i = start
    while i + 8 <= end:
        cid = buf[i:i + 4]
        size = struct.unpack("<I", buf[i + 4:i + 8])[0]
        yield cid, i + 8, i + 8 + size
        i = i + 8 + size + (size & 1)


def _find_inam(buf, start, end):
    """任意深度找 INAM（乐器名）。DLS 各版本层级不一样，所以递归。"""
    for cid, body, stop in _chunks(buf, start, end):
        if cid == b"INAM":
            return buf[body:stop].rstrip(b"\x00").decode("utf-8", "replace").strip()
        if cid == b"LIST":
            found = _find_inam(buf, body + 4, stop)
            if found:
                return found
    return None


GM_KIT_BANK = 0x80000000   # DLS 里鼓组所在的 bank（通道 10 上按 program 选的就是它）


def parse_dls(path=DLS_PATH, bank_filter=0):
    """解析 GM 音色库，返回 {program: name}。

    默认取 bank 0（旋律音色）；传 bank_filter=GM_KIT_BANK 取鼓组。
    """
    if not os.path.exists(path):
        raise SystemExit(f"找不到 GM 音色库：{path}\n这台机器可能没装 macOS 音频组件。")
    data = open(path, "rb").read()
    if data[:4] != b"RIFF" or data[8:12] != b"DLS ":
        raise SystemExit(f"{path} 不是 DLS 文件")
    total = 8 + struct.unpack("<I", data[4:8])[0]

    programs = {}
    for cid, body, stop in _chunks(data, 12, total):
        if cid != b"LIST" or data[body:body + 4] != b"lins":
            continue
        for cid2, body2, stop2 in _chunks(data, body + 4, stop):
            if cid2 != b"LIST" or data[body2:body2 + 4] != b"ins ":
                continue
            bank = program = None
            for cid3, body3, stop3 in _chunks(data, body2 + 4, stop2):
                if cid3 == b"insh":
                    _regions, bank, program = struct.unpack("<III", data[body3:body3 + 12])
                    break
            if bank != bank_filter or program is None:
                continue
            name = _find_inam(data, body2 + 4, stop2)
            if name:
                programs.setdefault(program, name)
    return programs


# ------------------------------------------------------------ Logic patch


def scan_patches(depth=WALK_DEPTH):
    """扫所有 patch 根，返回 [{root, patches:[(相对路径, 分类)], total}]。"""
    out = []
    for root in PATCH_ROOTS:
        if not os.path.isdir(root):
            out.append(dict(root=root, patches=[], total=0, missing=True))
            continue
        patches = []
        stack = [(root, 0)]
        while stack:
            current, level = stack.pop()
            try:
                entries = list(os.scandir(current))
            except OSError:
                continue
            for entry in entries:
                if not entry.is_dir(follow_symlinks=False):
                    continue
                if entry.name.endswith(".patch"):
                    rel = os.path.relpath(entry.path, root)[:-len(".patch")]
                    patches.append((rel, os.path.dirname(rel) or "(未分类)"))
                elif level < depth:
                    stack.append((entry.path, level + 1))
        patches.sort()
        out.append(dict(root=root, patches=patches, total=len(patches), missing=False))
    return out


def logic_version():
    try:
        with open("/Applications/Logic Pro.app/Contents/Info.plist", "rb") as f:
            info = plistlib.load(f)
        short = info.get("CFBundleShortVersionString", "")
        build = info.get("CFBundleVersion", "")
        return f"{short} ({build})" if short else "未知"
    except Exception:
        return "未知"


# ------------------------------------------------------------------ 渲染


def drum_slots():
    """哪些槽是鼓。以 compose.TRACKS 的 is_drum 为准，别在这里写死。"""
    from core.compose import TRACKS

    return {key for key, meta in TRACKS.items() if meta.get("is_drum")}


def _usage(program, drum_kits):
    """反查：这个号被我们哪些乐器用到。鼓组号要单独标注，别和旋律音色混为一谈。"""
    drums = drum_slots()
    used = []
    for slot, options in INSTRUMENTS.items():
        for key, entry in options.items():
            if slot in drums:
                if drum_kits.get(slot, {}).get(key) == program:
                    used.append(f"`{slot}.{key}`（鼓组）")
            elif entry.get("program") == program:
                used.append(f"`{slot}.{key}`")
    return used


def drum_kit_map():
    """{槽: {乐器: 鼓组号}}。鼓类槽（drums 与跟随它的 perc）都算。"""
    drums = drum_slots()
    kits = {}
    for slot, options in INSTRUMENTS.items():
        if slot not in drums:
            continue
        kits[slot] = {key: entry["program"] for key, entry in options.items()
                      if "program" in entry}
    # perc 这类跟随者没有自己的 program，复制 leader 的
    for slot, leader in KIT_SHARED.items():
        kits.setdefault(slot, dict(kits.get(leader, {})))
    return kits


def render_gm(programs, kits, version):
    from core.arrange import TRACK_KEYS

    drums = drum_slots()
    drum_kits = drum_kit_map()
    lines = [
        "# GM 音色对照表（本机导出）",
        "",
        "> 自动生成，别手改 —— 重新跑 `python tools/gen_references.py`。",
        "",
        f"- 数据来源：`{DLS_PATH}`",
        "- 这 128 个名字就是 macOS 自带 GM 音色库里的**实际名字**。",
        "  Logic 打开 `.mid` 时按 program 号取的就是这套音色（不是 Logic 音色库）。",
        f"- 生成时间：{datetime.date.today().isoformat()}　Logic 版本：{version}",
        "",
        "「我们用到的」指 `music/core/instruments.py` 里哪些乐器选项写的就是这个号。",
        "鼓组号（`drums` / `perc`）和旋律音色的号会重复，所以单独标「鼓组」——",
        "它们在同一条 MIDI 通道上含义不同：通道 10 的 program 选的是**鼓组**。",
        "",
        "| 号 | 族 | 本机音色名 | 我们用到的 |",
        "|---:|---|---|---|",
    ]
    for program in range(128):
        name = programs.get(program)
        if not name:
            continue
        family = GM_FAMILIES[program // 8] if program // 8 < len(GM_FAMILIES) else "?"
        used = "、".join(_usage(program, drum_kits))
        lines.append(f"| {program} | {family} | {name} | {used} |")

    lines += [
        "",
        "## 我们实际用到的号（逐槽展开）",
        "",
        "| 槽 | 乐器 | program | 本机音色名 |",
        "|---|---|---:|---|",
    ]
    for slot in TRACK_KEYS:
        for key, entry in INSTRUMENTS[slot].items():
            if slot in drums:
                program = drum_kits.get(slot, {}).get(key)
                if slot in KIT_SHARED:
                    # perc 自己没有 program，运行时复制 drums 的鼓组号
                    note = f"跟随 `{KIT_SHARED[slot]}` 的鼓组"
                else:
                    note = f"`{kits.get(program, '?')}`（本槽决定鼓组）"
                lines.append(
                    f"| `{slot}` | `{key}` | {program if program is not None else '—'} | {note} |"
                )
                continue
            program = entry["program"]
            lines.append(f"| `{slot}` | `{key}` | {program} | {programs.get(program, '?')} |")

    lines += [
        "",
        "## 鼓组号（通道 10，和上面的旋律音色是两套）",
        "",
        "`drums` 与 `perc` 都落在 MIDI 通道 10。**同一个号在这条通道上是鼓组，",
        "在别的通道上是旋律音色** —— 这就是为什么 0 号既叫 “Piano 1” 又叫 “Standard”。",
        "",
        "| program | 本机鼓组名 | 我们用到的 |",
        "|---:|---|---|",
    ]
    for program in sorted(kits):
        used = [f"`{slot}.{key}`" for slot, mapping in drum_kits.items()
                for key, value in mapping.items() if value == program]
        lines.append(f"| {program} | {kits[program]} | {'、'.join(used) or ''} |")

    lines += ["", "## 编制预设用到的号", ""]
    for preset, mapping in PRESETS.items():
        parts = []
        for slot, key in mapping.items():
            entry = INSTRUMENTS[slot][key]
            program = entry.get("program")
            if program is None:
                parts.append(f"`{slot}`={entry['name']}（鼓组随 `{KIT_SHARED.get(slot, '?')}`）")
            else:
                parts.append(f"`{slot}`={entry['name']}（{program} → {programs.get(program, '?')}）")
        lines.append(f"- **{preset}**：" + "；".join(parts))
    return "\n".join(lines) + "\n"


def render_patches(roots):
    lines = [
        "# Logic 乐器 patch 清单（本机导出）",
        "",
        "> 自动生成，别手改 —— 重新跑 `python tools/gen_references.py`。",
        "",
        "这些是 Logic 的 Library 面板里能直接点到的**音色**（和我们 MIDI 里的 GM 号是两回事）。",
        "装了新的音色库之后重跑一次，这份表就会更新。",
        "",
        f"生成时间：{datetime.date.today().isoformat()}　Logic 版本：{logic_version()}",
        "",
        "## 库根与规模",
        "",
        "| 库根 | patch 数 |",
        "|---|---:|",
    ]
    for entry in roots:
        root = entry["root"].replace(os.path.expanduser("~"), "~")
        count = "未找到" if entry["missing"] else str(entry["total"])
        lines.append(f"| `{root}` | {count} |")

    lines += ["", "## 分类规模", "", "| 分类 | patch 数 |", "|---|---:|"]
    counts = {}
    for entry in roots:
        for _rel, category in entry["patches"]:
            top = category.split(os.sep)[0]
            counts[top] = counts.get(top, 0) + 1
    for top, count in sorted(counts.items(), key=lambda kv: -kv[1]):
        lines.append(f"| {top} | {count} |")

    lines += [
        "",
        "## 每个槽该去哪里找（按关键词命中本机 patch）",
        "",
        "关键词是本工程给每个功能槽预设的检索词；命中数指本机实际存在的 patch。",
        "",
        "| 槽 | 关键词 | 命中 | 几个例子 |",
        "|---|---|---:|---|",
    ]
    all_patches = [(rel, root["root"]) for root in roots for rel, _cat in root["patches"]]
    for slot, words in SLOT_KEYWORDS.items():
        hits = []
        seen = set()
        for rel, _root in all_patches:
            # 鼓组的 patch 名字里也有 bell / horn / vocal，别让它们污染旋律槽的候选
            if slot not in ("drums", "perc") and "Drums & Percussion" in rel:
                continue
            base = os.path.basename(rel)
            if base in seen:
                continue
            if any(word in base.lower() for word in words):
                seen.add(base)
                hits.append(rel)
        examples = "、".join(f"`{os.path.basename(p)}`" for p in hits[:4]) or "—"
        lines.append(f"| `{slot}` | {' / '.join(words[:4])}… | {len(hits)} | {examples} |")

    lines += [
        "",
        "> 这些只是「本机能搜到」的候选，不是「该用哪个」。选音色是审美判断，",
        "> 参考 `docs/music_knowledge/04-MIDI到Logic的乐器对应.md` 里的判断标准。",
    ]
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description="从本机导出 GM 音色与 Logic patch 参考表")
    parser.add_argument("--list-dls", action="store_true", help="只打印 GM 解析结果")
    parser.add_argument("--out", default=OUT_DIR, help="输出目录")
    args = parser.parse_args(argv)

    programs = parse_dls()
    kits = parse_dls(bank_filter=GM_KIT_BANK)
    print(f"[dls] 解析到 {len(programs)} 个 GM 音色（bank 0）、{len(kits)} 个鼓组（bank 0x80000000）")

    if args.list_dls:
        for program in range(128):
            print(f"  {program:>3}  {programs.get(program, '?')}")
        return 0

    roots = scan_patches()
    for entry in roots:
        state = "未找到" if entry["missing"] else f"{entry['total']} 个 patch"
        print(f"[logic] {entry['root']} → {state}")

    version = logic_version()
    print(f"[logic] 版本 {version}")

    os.makedirs(args.out, exist_ok=True)
    files = {
        "gm-programs.md": render_gm(programs, kits, version),
        "logic-patches.md": render_patches(roots),
    }
    for name, text in files.items():
        path = os.path.join(args.out, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"已写: {os.path.relpath(path, _ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
