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
