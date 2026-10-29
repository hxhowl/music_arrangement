import pytest

from core.theory import (
    build_progression,
    default_progression,
    degree_to_chord,
    fold_into_range,
    parse_key,
    parse_note,
    voice_lead,
)


class TestParseKey:
    def test_major_and_minor(self):
        assert parse_key("C") == ("C", "major")
        assert parse_key("Am") == ("A", "minor")
        assert parse_key("F#m") == ("F#", "minor")
        assert parse_key("Bb") == ("Bb", "major")

    def test_rejects_garbage(self):
        with pytest.raises(ValueError):
            parse_key("Hm")
        with pytest.raises(ValueError):
            parse_key("")

    def test_rejects_unknown_mode(self):
        with pytest.raises(ValueError):
            parse_key("Adorian")


class TestDegreeToChord:
    def test_minor_key_minor_one(self):
        assert degree_to_chord("Am", "i") == ("Am", [0, 3, 7])

    def test_flat_spelling_follows_key(self):
        # D 小调的 VI 级必须写成 Bb，不是 A#
        name, intervals = degree_to_chord("Dm", "VI")
        assert name == "Bb"
        assert intervals == [0, 4, 7]

    def test_sharp_key(self):
        assert degree_to_chord("F#m", "i")[0] == "F#m"
        assert degree_to_chord("F#m", "VII")[0] == "E"

    def test_seventh(self):
        name, intervals = degree_to_chord("Am", "i", seventh=True)
        assert name == "Am7"
        assert intervals == [0, 3, 7, 10]

    def test_bad_degree(self):
        with pytest.raises(ValueError):
            degree_to_chord("Am", "VIII")


class TestProgression:
    def test_default_minor_matches_legacy(self):
        # 旧版写死的 F#m-D-A-E 必须原样复现
        names, _ = build_progression("F#m", ["i", "VI", "III", "VII"])
        assert names == ["F#m", "D", "A", "E"]

    def test_default_progression_by_mode(self):
        assert default_progression("Am") == ["i", "VI", "III", "VII"]
        assert default_progression("C") == ["I", "V", "vi", "IV"]

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            build_progression("Am", [])


class TestPitchHelpers:
    def test_parse_note_supports_flats_and_double_sharps(self):
        assert parse_note("C") == 0
        assert parse_note("Bb") == 10
        assert parse_note("F#") == 6
        assert parse_note("C##") == 2

    def test_fold_into_range(self):
        assert fold_into_range(26, 33, 44) == 38
        assert fold_into_range(55, 33, 44) == 43


class TestVoiceLeading:
    def test_moves_less_than_root_position(self):
        # F#m -> D 的和弦音级
        first = voice_lead([6, 9, 1], None, 48, 67)
        second = voice_lead([2, 6, 9], first, 48, 67)
        assert len(second) == 3
        # 声部移动总量应该很小（这就是 voice leading 的意义）
        assert sum(abs(a - b) for a, b in zip(sorted(first), sorted(second))) <= 6

    def test_stays_inside_range(self):
        voicing = voice_lead([0, 4, 7], None, 50, 60)
        assert all(50 <= p <= 60 for p in voicing)
