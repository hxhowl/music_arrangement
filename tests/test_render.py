import mido
import pretty_midi

from core.compose import TRACKS, compose
from core.report import check


def _load(path):
    return pretty_midi.PrettyMIDI(str(path))


def _notes(path, track):
    pm = _load(path)
    for inst in pm.instruments:
        if inst.name == track:
            return inst.notes
    return []


def _collisions(a, b):
    seen = set()
    for x in a:
        for y in b:
            if x.pitch == y.pitch and x.start < y.end and y.start < x.start + 1e-9:
                seen.add((round(x.start, 2), x.pitch))
    return len(seen)


class TestOutputShape:
    def test_format_and_tracks(self, make_project):
        project = make_project()
        path, ok = compose(str(project), "v1", report=False)[0]
        assert ok

        midi = mido.MidiFile(path)
        assert midi.type == 1
        assert midi.ticks_per_beat == 960

        pm = _load(path)
        assert {i.name for i in pm.instruments} == set(TRACKS)

    def test_bar_length_matches_config(self, make_project):
        project = make_project(sections={"verse": 2, "chorus": 2}, bpm=120)
        path, _ = compose(str(project), "v1", report=False)[0]
        bar_seconds = 4 * 60 / 120
        assert abs(_load(path).get_end_time() / bar_seconds - 4) < 0.6

    def test_snapshot_written(self, make_project):
        project = make_project(seed=3)
        compose(str(project), "v1", report=False)
        assert (project / "music" / "output" / f"{project.name}-v1.config.json").exists()


class TestDeterminism:
    def test_same_seed_same_bytes(self, make_project):
        project = make_project(seed=0)
        first, _ = compose(str(project), "v1", report=False)[0]
        second, _ = compose(str(project), "v2", report=False)[0]
        assert open(first, "rb").read() == open(second, "rb").read()

    def test_different_seed_differs(self, make_project):
        project = make_project(seed=0)
        plain, _ = compose(str(project), "v1", report=False)[0]
        moved, _ = compose(str(project), "v2", report=False, seed=7)[0]
        assert open(plain, "rb").read() != open(moved, "rb").read()

    def test_takes_produce_distinct_versions(self, make_project):
        project = make_project(sections={"verse": 2, "chorus": 2})
        results = compose(str(project), "v1", report=False, takes=3)
        assert len(results) == 3
        blobs = {open(p, "rb").read() for p, _ in results}
        assert len(blobs) == 3


class TestSectionStyle:
    def test_only_overridden_section_changes(self, make_project):
        base = make_project(sections={"verse": 4, "chorus": 4})
        plain, _ = compose(str(base), "v1", report=False)[0]

        with_style = make_project(
            sections={"verse": 4, "chorus": 4},
            arrange={"chorus": {"style": "playful"}},
        )
        mixed, _ = compose(str(with_style), "v1", report=False)[0]

        def sig(notes, start, end):
            return [
                (n.pitch, round(n.start, 2), round(n.end - n.start, 2), n.velocity)
                for n in notes if start <= n.start < end
            ]

        bar = 4 * 60 / 100
        for track in ("chords", "bass", "pad", "lead"):
            same_verse = sig(_notes(plain, track), 0, 4 * bar)
            assert same_verse == sig(_notes(mixed, track), 0, 4 * bar), \
                f"{track} 主歌不该被影响"

            base_chorus = sig(_notes(plain, track), 4 * bar, 8 * bar)
            mixed_chorus = sig(_notes(mixed, track), 4 * bar, 8 * bar)
            assert base_chorus != mixed_chorus, f"{track} 副歌应该换风格"


class TestMix:
    def test_no_melody_unison_collisions(self, make_project):
        project = make_project(sections={"verse": 2, "chorus": 4, "outro": 2})
        path, _ = compose(str(project), "v1", report=False)[0]
        lead = _notes(path, "lead")
        for track in ("pad", "arp", "chords"):
            assert _collisions(lead, _notes(path, track)) == 0, f"lead 与 {track} 同音高"

    def test_pad_yields_to_melody(self, make_project):
        with_lead = make_project(sections={"verse": 2, "chorus": 4})
        path, _ = compose(str(with_lead), "v1", report=False)[0]
        bar = 4 * 60 / 100
        chorus_pad = [n for n in _notes(path, "pad") if n.start >= 2 * bar]
        # 副歌有旋律，pad 应该被压过 + 让过音，不会出现满编的三音长音
        assert max(n.velocity for n in chorus_pad) <= 45


class TestReport:
    def test_passes_on_generated_song(self, make_project, capsys):
        project = make_project()
        path, _ = compose(str(project), "v1", report=False)[0]
        from core.config import load_config
        from core.theory import build_progression

        cfg = load_config(str(project))
        progression, _ = build_progression(cfg["key"], cfg["progression"])
        assert check(path, cfg, progression) is True

    def test_detects_collision(self, make_project, capsys):
        project = make_project()
        path, _ = compose(str(project), "v1", report=False)[0]
        from core.config import load_config
        from core.theory import build_progression

        cfg = load_config(str(project))
        progression, _ = build_progression(cfg["key"], cfg["progression"])

        pm = _load(path)
        pm.instruments = [i for i in pm.instruments if i.name in ("lead", "pad")]
        for inst in pm.instruments:
            for note in inst.notes:
                note.pitch = 60
        broken = project / "music" / "output" / "broken.mid"
        pm.write(str(broken))

        check(str(broken), cfg, progression)
        assert "同音高" in capsys.readouterr().out
