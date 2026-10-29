import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "music") not in sys.path:
    sys.path.insert(0, str(ROOT / "music"))


@pytest.fixture
def make_project(tmp_path):
    """在临时目录建一个最小项目，返回项目路径。

    每次调用都建一个新目录（song1 / song2 …），否则同一个测试里建两个项目
    会互相覆盖 config.json。
    """
    counter = {"n": 0}

    def _make(**overrides):
        cfg = {
            "bpm": 100,
            "key": "Am",
            "seed": 0,
            "progression": ["i", "VI", "III", "VII"],
            "style": "pop",
            "time_sig": [4, 4],
            "sections": {"verse": 2, "chorus": 2},
            "velocity_base": 80,
        }
        cfg.update(overrides)

        counter["n"] += 1
        project = tmp_path / f"song{counter['n']}"
        (project / "music" / "output").mkdir(parents=True, exist_ok=True)
        (project / "config.json").write_text(
            json.dumps(cfg, ensure_ascii=False), encoding="utf-8"
        )
        return project

    return _make
