"""乐器选择：注册表完整性、预设与覆盖优先级、演奏法微调是否真的生效。"""

import copy

import pretty_midi
import pytest

from core.arrange import TRACK_KEYS
from core.compose import compose
from core.config import load_config
from core.instruments import (
    DEFAULT,
    INSTRUMENTS,
    KIT_SHARED,
    PRESETS,
    SLOTS,
    STYLE_PRESET,
    get,
    merge_tweaks,
    plan,
    tweaks_of,
)
from core.styles import STYLES


def _notes(path, track):
    pm = pretty_midi.PrettyMIDI(str(path))
    for inst in pm.instruments:
        if inst.name == track:
            return inst
    return None


class TestRegistry:
    def test_slots_match_tracks(self):
        assert set(SLOTS) == set(TRACK_KEYS)

    def test_every_slot_has_default_and_options(self):
        for slot in SLOTS:
            assert DEFAULT[slot] in INSTRUMENTS[slot], f"{slot} 的默认乐器不在可选列表"
            assert len(INSTRUMENTS[slot]) >= 2, f"{slot} 只有一个选项，等于没得选"

    def test_entries_are_complete(self):
        for slot, options in INSTRUMENTS.items():
            for key, entry in options.items():
                if slot in KIT_SHARED:
                    assert "program" not in entry, f"{slot}.{key} 不该自带 program"
                else:
                    assert 0 <= entry["program"] <= 127, f"{slot}.{key} program 越界"
                assert entry["name"] and entry["why"], f"{slot}.{key} 缺 name/why"
                for group in entry.get("tweaks") or {}:
                    assert group in TRACK_KEYS, f"{slot}.{key} 的 tweaks 指向未知分组 {group}"

    def test_presets_cover_all_slots(self):
        for name, mapping in PRESETS.items():
            assert set(mapping) == set(SLOTS), f"预设 {name} 没配齐 8 个槽"

    def test_style_presets_exist(self):
        for style, preset in STYLE_PRESET.items():
            assert style in STYLES
            assert preset in PRESETS


class TestResolve:
    def test_unknown_slot_lists_slots(self):
        with pytest.raises(KeyError, match="chords"):
            get("guitar", "nylon")

    def test_unknown_instrument_lists_options(self):
        with pytest.raises(KeyError, match="nylon"):
            get("chords", "sitar")

    def test_plan_default_is_backward_compatible(self):
        # 老项目没有 preset / instruments 字段，行为必须和以前一致
        assert plan({})["chords"]["program"] == 0
        assert plan({})["bass"]["program"] == 33

    def test_preset_applies(self):
        chosen = plan({"preset": "cinematic"})
        assert chosen["chords"]["key"] == "strings"
        assert chosen["chords"]["program"] == 48

    def test_instruments_override_preset(self):
        chosen = plan({"preset": "cinematic", "instruments": {"chords": "piano"}})
        assert chosen["chords"]["key"] == "piano"
        assert chosen["pad"]["key"] == "strings", "没被覆盖的槽应该还跟着预设"

    def test_unknown_preset(self):
        with pytest.raises(ValueError, match="未知编制预设"):
            plan({"preset": "orchestra"})

    def test_unknown_slot_in_config(self):
        with pytest.raises(ValueError, match="未知功能槽"):
            plan({"instruments": {"guitar": "nylon"}})

    def test_plan_does_not_touch_global(self):
        before = copy.deepcopy(INSTRUMENTS)
        chosen = plan({"preset": "lofi"})
        chosen["chords"]["program"] = 99
        assert INSTRUMENTS == before

    def test_perc_follows_drum_kit(self):
        """perc 和 drums 共用通道 10，只能有一个鼓组号，必须一致。"""
        for cfg in ({}, {"preset": "cinematic"}, {"preset": "electronic"}):
            chosen = plan(cfg)
            assert chosen["perc"]["program"] == chosen["drums"]["program"], cfg
        assert plan({"preset": "cinematic"})["perc"]["program"] == 8  # Room 鼓组
        assert KIT_SHARED == {"perc": "drums"}


class TestTweaks:
    def test_collects_from_all_slots(self):
        got = tweaks_of(plan({"preset": "cinematic"}))
        assert got["chords"]["hold"] == 0.99
        assert got["pad"]["hold"] == 0.99
        assert got["perc"]["gm"] == "shaker"

    def test_explicit_config_wins(self):
        merged = merge_tweaks({"chords": {"hold": 0.5}}, {"chords": {"hold": 0.99}})
        assert merged["chords"]["hold"] == 0.5, "config.style_tweaks 应该压过乐器自带"

    def test_unrelated_groups_survive(self):
        merged = merge_tweaks({"bass": {"velocity": 70}}, {"pad": {"hold": 0.99}})
        assert merged["bass"]["velocity"] == 70
        assert merged["pad"]["hold"] == 0.99


class TestRender:
    def test_program_written_into_midi(self, make_project):
        project = make_project(instruments={"chords": "nylon"})
        path, _ = compose(str(project), "v1", report=False)[0]
        assert _notes(path, "chords").program == 24

    def test_preset_changes_all_pitched_tracks(self, make_project):
        project = make_project(preset="cinematic")
        path, _ = compose(str(project), "v1", report=False)[0]
        assert _notes(path, "lead").program == 40     # 小提琴
        assert _notes(path, "counter").program == 60  # 圆号

    def test_instrument_tweak_changes_note_length(self, make_project):
        """换乐器不只换 program，弹法也要跟着变——这是"换音色不换弹法"的解药。"""
        plain = make_project()
        nylon = make_project(instruments={"chords": "nylon"})
        strings = make_project(instruments={"chords": "strings"})

        def first_chord_len(path):
            inst = _notes(path, "chords")
            return inst.notes[0].end - inst.notes[0].start

        a = first_chord_len(compose(str(plain), "v1", report=False)[0][0])
        b = first_chord_len(compose(str(nylon), "v1", report=False)[0][0])
        c = first_chord_len(compose(str(strings), "v1", report=False)[0][0])

        assert b < a < c, f"尼龙弦({b:.2f}) 应短于钢琴({a:.2f})，弦乐群({c:.2f}) 应更长"

    def test_explicit_style_tweak_beats_instrument(self, make_project):
        project = make_project(
            instruments={"chords": "nylon"},       # 自带 hold=0.66
            style_tweaks={"chords": {"hold": 0.95}},  # 显式指定
        )
        path, _ = compose(str(project), "v1", report=False)[0]
        inst = _notes(path, "chords")
        bar = 4 * 60 / 100
        dur = (inst.notes[0].end - inst.notes[0].start) / bar
        assert 0.9 < dur < 1.0, "显式 style_tweaks 应该生效"

    def test_drum_kit_not_overwritten_by_perc(self, make_project):
        """回归：drums 与 perc 同在通道 10，后写的 program_change 会覆盖前者。

        曾经的症状：cinematic 预设选 Room 鼓组(8)，导进 Logic 却是标准鼓组(0)，
        因为 perc 轨在 drums 之后又写了一次 program_change。
        """
        import mido

        project = make_project(preset="cinematic")
        path, _ = compose(str(project), "v1", report=False)[0]
        kits = {}
        for track in mido.MidiFile(str(path)).tracks:
            for msg in track:
                if msg.type == "program_change" and msg.channel == 9:
                    kits.setdefault(msg.program, []).append(track.name)
        assert list(kits) == [8], f"通道 10 上出现了多个鼓组号：{kits}"


class TestConfigValidation:
    def test_bad_preset_rejected_early(self, make_project):
        with pytest.raises(ValueError, match="未知编制预设"):
            load_config(str(make_project(preset="orchestra")))

    def test_bad_instrument_rejected_early(self, make_project):
        with pytest.raises(KeyError, match="sitar"):
            load_config(str(make_project(instruments={"chords": "sitar"})))

    def test_bad_slot_rejected_early(self, make_project):
        with pytest.raises(ValueError, match="未知功能槽"):
            load_config(str(make_project(instruments={"guitar": "nylon"})))
