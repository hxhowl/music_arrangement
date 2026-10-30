"""references/ 里的参考表必须和代码一致。

`references/gm-programs.md` 是从本机导出的（`tools/gen_references.py`），
但它是**静态文件**：改了 `music/core/instruments.py` 里的 program 号却忘了重跑，
这份"参考"就会开始骗人 —— 比没有更糟。所以这里对齐一次。

这个测试只读文件，不依赖 macOS 路径，CI 上也能跑。
"""

import os
import re

import pytest

from core.instruments import INSTRUMENTS, KIT_SHARED

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF_DIR = os.path.join(ROOT, "references")


def _read(name):
    path = os.path.join(REF_DIR, name)
    assert os.path.exists(path), f"{name} 不存在，先跑 python tools/gen_references.py"
    with open(path, encoding="utf-8") as f:
        return f.read()


def _per_slot_rows(text):
    """取「我们实际用到的号（逐槽展开）」那张表，返回 {(槽, 乐器): program 或 None}。"""
    body = text.split("## 我们实际用到的号", 1)[1].split("## 鼓组号", 1)[0]
    rows = {}
    for line in body.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 4 or not cells[0].startswith("`"):
            continue
        slot = cells[0].strip("`")
        key = cells[1].strip("`")
        program = cells[2]
        rows[(slot, key)] = None if program in ("—", "-", "") else int(program)
    return rows


class TestGmTable:
    def test_covers_every_instrument(self):
        rows = _per_slot_rows(_read("gm-programs.md"))
        expected = {(slot, key) for slot, options in INSTRUMENTS.items() for key in options}
        missing = expected - set(rows)
        extra = set(rows) - expected
        assert not missing, f"参考表缺这些乐器（重跑 gen_references.py）：{sorted(missing)}"
        assert not extra, f"参考表有多余条目（乐器已删除？）：{sorted(extra)}"

    def test_program_numbers_match_code(self):
        rows = _per_slot_rows(_read("gm-programs.md"))
        wrong = []
        for slot, options in INSTRUMENTS.items():
            for key, entry in options.items():
                got = rows.get((slot, key))
                want = entry.get("program")
                if got != want:
                    wrong.append(f"{slot}.{key}: 表里 {got} ≠ 代码 {want}")
        assert not wrong, "参考表的号与代码不一致（重跑 gen_references.py）：\n  " + "\n  ".join(wrong)

    def test_kit_slots_have_no_program(self):
        """鼓组跟随者（perc）不该有自己的号 —— 有了就会在通道 10 上打架。"""
        rows = _per_slot_rows(_read("gm-programs.md"))
        for slot in KIT_SHARED:
            for key in INSTRUMENTS[slot]:
                assert rows[(slot, key)] is None, f"{slot}.{key} 不该有 program"

    def test_all_128_programs_listed(self):
        text = _read("gm-programs.md")
        table = text.split("| 号 | 族 | 本机音色名 | 我们用到的 |", 1)[1].split("##", 1)[0]
        numbers = {int(m) for m in re.findall(r"^\|\s*(\d+)\s*\|", table, re.M)}
        assert numbers == set(range(128)), "GM 表不全（应该有 0~127）"

    def test_drum_kits_listed(self):
        text = _read("gm-programs.md")
        assert "## 鼓组号" in text
        for kit in ("Standard", "Room", "Power", "Electronic", "Brush"):
            assert f"| {kit} |" in text, f"鼓组表缺 {kit}"


class TestHandWrittenDocs:
    def test_logic_import_covers_all_slots(self):
        text = _read("logic-import.md")
        for slot in INSTRUMENTS:
            assert f"### {slot}（" in text or f"### {slot}" in text, f"对照表缺 {slot}"

    def test_every_instrument_mentioned(self):
        """每个可选乐器都要能在对照表里查到，否则用户选了没文档。"""
        text = _read("logic-import.md")
        missing = [
            f"{slot}.{key}"
            for slot, options in INSTRUMENTS.items()
            for key in options
            if f"`{key}`" not in text
        ]
        assert not missing, f"logic-import.md 里没提到：{missing}"

    def test_patch_table_exists(self):
        assert "patch 数" in _read("logic-patches.md")


if __name__ == "__main__":
    pytest.main([__file__])
