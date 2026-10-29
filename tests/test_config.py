import json

import pytest

from core.config import DEFAULT_CONFIG, load_config


class TestLoad:
    def test_missing_file_falls_back_with_warning(self, tmp_path, capsys):
        cfg = load_config(str(tmp_path))
        assert cfg["bpm"] == DEFAULT_CONFIG["bpm"]
        assert "未找到" in capsys.readouterr().out

    def test_project_file_wins(self, make_project):
        project = make_project(bpm=132, key="Dm")
        cfg = load_config(str(project))
        assert cfg["bpm"] == 132
        assert cfg["key"] == "Dm"

    def test_progression_defaults_by_mode(self, make_project):
        project = make_project(key="C")
        # 删掉 progression，让它按调式补
        path = project / "config.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data.pop("progression")
        path.write_text(json.dumps(data), encoding="utf-8")

        cfg = load_config(str(project))
        assert cfg["progression"] == ["I", "V", "vi", "IV"]

    def test_sections_are_replaced_not_merged(self, make_project):
        project = make_project(sections={"intro": 2})
        cfg = load_config(str(project))
        assert cfg["sections"] == {"intro": 2}


class TestValidation:
    def test_bad_style(self, make_project):
        with pytest.raises(ValueError, match="未知风格"):
            load_config(str(make_project(style="techno")))

    def test_bad_bpm(self, make_project):
        with pytest.raises(ValueError, match="bpm"):
            load_config(str(make_project(bpm=9)))

    def test_non_numeric_bpm(self, make_project):
        with pytest.raises(ValueError, match="不是数字"):
            load_config(str(make_project(bpm=None)))

    def test_bad_seed(self, make_project):
        with pytest.raises(ValueError, match="seed"):
            load_config(str(make_project(seed=-1)))

    def test_three_four_rejected(self, make_project):
        with pytest.raises(NotImplementedError, match="4/4"):
            load_config(str(make_project(time_sig=[3, 4])))

    def test_swing_rejected(self, make_project):
        with pytest.raises(NotImplementedError, match="swing"):
            load_config(str(make_project(swing=0.2)))

    def test_empty_sections(self, make_project):
        with pytest.raises(ValueError, match="sections"):
            load_config(str(make_project(sections={})))

    def test_bad_bars(self, make_project):
        with pytest.raises(ValueError, match="正整数"):
            load_config(str(make_project(sections={"verse": "4"})))
