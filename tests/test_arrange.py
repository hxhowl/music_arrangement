import pytest

from core.arrange import ARRANGE, active_tracks, get, validate_overrides


class TestArrangeDefaults:
    def test_defaults_present(self):
        arr = get("chorus")
        assert arr["drums"] == "full"
        assert arr["lead"] is True
        assert arr["crash"] is True
        assert arr["style"] is None

    def test_unknown_section_raises(self):
        with pytest.raises(KeyError, match="未知段落"):
            get("drop")

    def test_active_tracks(self):
        tracks = active_tracks(["intro", "chorus"])
        assert "lead" in tracks
        assert "arp" in tracks
        assert "perc" in tracks


class TestOverrides:
    def test_partial_override(self):
        arr = get("chorus", {"chorus": {"drums": "medium"}})
        assert arr["drums"] == "medium"
        assert arr["lead"] is True, "没覆盖的字段应保持默认"

    def test_section_style(self):
        arr = get("chorus", {"chorus": {"style": "playful"}})
        assert arr["style"] == "playful"

    def test_unknown_field_raises(self):
        with pytest.raises(ValueError, match="未知字段"):
            get("chorus", {"chorus": {"drumz": "full"}})

    def test_bad_density_raises(self):
        with pytest.raises(ValueError, match="不合法"):
            get("chorus", {"chorus": {"drums": "loud"}})

    def test_bad_style_raises(self):
        with pytest.raises(ValueError, match="未知"):
            get("chorus", {"chorus": {"style": "techno"}})

    def test_counter_voice_default_is_none(self):
        """默认交给风格决定，编排层不硬塞一个声部。"""
        assert get("chorus")["counter_voice"] is None

    def test_counter_voice_override(self):
        arr = get("chorus", {"chorus": {"counter": True, "counter_voice": "high"}})
        assert arr["counter"] is True
        assert arr["counter_voice"] == "high"

    def test_bad_counter_voice_raises(self):
        with pytest.raises(ValueError, match="counter_voice"):
            get("chorus", {"chorus": {"counter_voice": "middle"}})

    def test_build_defaults(self):
        assert get("chorus")["build"] == "up", "副歌默认渐强"
        assert get("verse")["build"] is None

    def test_build_override(self):
        assert get("verse", {"verse": {"build": "down"}})["build"] == "down"

    def test_bad_build_raises(self):
        with pytest.raises(ValueError, match="build"):
            get("verse", {"verse": {"build": "louder"}})

    def test_non_bool_flag_raises(self):
        with pytest.raises(ValueError, match="true/false"):
            get("chorus", {"chorus": {"crash": "yes"}})

    def test_vel_coerced_to_float(self):
        arr = get("chorus", {"chorus": {"vel": "0.9"}})
        assert arr["vel"] == 0.9

    def test_validate_overrides_walks_everything(self):
        validate_overrides({"chorus": {"drums": "medium"}})
        with pytest.raises(ValueError):
            validate_overrides({"chorus": {"drums": "loud"}})

    def test_default_arrange_not_mutated(self):
        before = dict(ARRANGE["chorus"])
        get("chorus", {"chorus": {"drums": "medium", "vel": 0.5}})
        assert ARRANGE["chorus"] == before
