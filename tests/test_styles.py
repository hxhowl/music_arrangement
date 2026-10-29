import copy

import pytest

from core.styles import STYLES, names, resolve


class TestResolve:
    def test_every_style_is_valid(self):
        for name in names():
            spec = resolve(name)
            assert set(spec) >= {
                "chords", "bass", "drums", "lead", "pad",
                "fill", "fill_every", "ghost", "humanize", "perc", "arp", "counter", "counter",
            }

    def test_tweaks_do_not_touch_global(self):
        before = copy.deepcopy(STYLES["pop"])
        spec = resolve("pop", {"bass": {"velocity": 10}})
        assert spec["bass"]["velocity"] == 10
        assert STYLES["pop"] == before, "resolve 不能改全局 STYLES"

    def test_tweak_scalar_field(self):
        spec = resolve("pop", {"fill_every": 8})
        assert spec["fill_every"] == 8
        assert STYLES["pop"]["fill_every"] == 4

    def test_unknown_group_rejected(self):
        with pytest.raises(ValueError, match="未知分组"):
            resolve("pop", {"guitar": {"x": 1}})

    def test_unknown_field_rejected(self):
        with pytest.raises(ValueError, match="未知字段"):
            resolve("pop", {"bass": {"velocty": 70}})

    def test_bad_humanize_sway_rejected(self):
        with pytest.raises(ValueError, match="humanize.sway"):
            resolve("pop", {"humanize": {"sway": 0.5}})

    def test_narrow_bass_range_rejected(self):
        with pytest.raises(ValueError, match="太窄"):
            resolve("pop", {"bass": {"low": 40, "high": 42}})

    def test_unknown_drum_piece_rejected(self):
        with pytest.raises(ValueError, match="未知鼓件"):
            resolve("pop", {"drums": {"full": [("kickk", 0.0, 0.1, 90)]}})

    def test_bad_perc_rejected(self):
        with pytest.raises(ValueError, match="perc.gm"):
            resolve("pop", {"perc": {"gm": "cowbell_x"}})
