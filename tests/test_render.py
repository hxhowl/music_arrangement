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

    def test_warns_when_overwriting_a_version(self, make_project, capsys):
        """显式指定已有版本号会覆盖旧版 —— 这是唯一会丢历史的路径，必须出声。"""
        project = make_project(seed=0)
        compose(str(project), "v1", report=False)
        capsys.readouterr()
        compose(str(project), "v1", report=False)
        assert "覆盖已存在" in capsys.readouterr().out

    def test_no_warning_for_new_version(self, make_project, capsys):
        project = make_project(seed=0)
        compose(str(project), "v1", report=False)
        compose(str(project), "v2", report=False)
        assert "覆盖已存在" not in capsys.readouterr().out


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


class TestHarmonicRhythm:
    def test_two_chords_per_bar(self, make_project):
        project = make_project(harmonic_rhythm=2, style="pop")
        path, _ = compose(str(project), "v1", report=False)[0]

        bar = 4 * 60 / 100
        chords = _notes(path, "chords")
        first = [n for n in chords if n.start < bar]
        # 半小节换和弦 → 一小节两组三和弦
        assert len(first) == 6

        starts = sorted({round((n.start) / bar, 2) for n in first})
        assert 0.0 in starts and 0.5 in starts

        def pcs(notes):
            return {n.pitch % 12 for n in notes}

        head = pcs([n for n in first if n.start < bar * 0.5])
        tail = pcs([n for n in first if n.start >= bar * 0.5])
        assert head != tail, "后半小节应该换了和弦"

    def test_one_chord_per_two_bars(self, make_project):
        # 单个长段落：段落切换会把和弦进行从头开始，测不出"两小节一个和弦"
        project = make_project(harmonic_rhythm=8, style="pop", sections={"verse": 6})
        path, _ = compose(str(project), "v1", report=False)[0]

        bar = 4 * 60 / 100
        chords = _notes(path, "chords")

        def pcs(b):
            return {n.pitch % 12 for n in chords if b * bar <= n.start < (b + 1) * bar}

        assert pcs(0) == pcs(1), "8 拍一个和弦：前两小节同和弦"
        assert pcs(1) != pcs(2), "第三小节才换"

    def test_bass_follows_mid_bar_change(self, make_project):
        plain = make_project(harmonic_rhythm=4)
        half = make_project(harmonic_rhythm=2)

        a = _notes(compose(str(plain), "v1", report=False)[0][0], "bass")
        b = _notes(compose(str(half), "v1", report=False)[0][0], "bass")

        bar = 4 * 60 / 100
        # 一小节一个和弦时，第 3 拍还是同一个根音；半小节换和弦后应该变了
        beat3_a = [n.pitch for n in a if bar * 0.7 <= n.start < bar * 0.8]
        beat3_b = [n.pitch for n in b if bar * 0.7 <= n.start < bar * 0.8]
        assert beat3_a and beat3_b
        assert beat3_a[0] != beat3_b[0]


class TestSwing:
    def test_only_offbeats_move(self, make_project):
        straight = make_project(swing=0)
        swung = make_project(swing=0.6)

        a = sorted(round(n.start, 4) for n in
                   _notes(compose(str(straight), "v1", report=False)[0][0], "bass"))
        b = sorted(round(n.start, 4) for n in
                   _notes(compose(str(swung), "v1", report=False)[0][0], "bass"))

        beat = 60 / 100
        expected = 0.6 * beat / 6
        shifts = [round(y - x, 4) for x, y in zip(a, b)]

        assert set(shifts) <= {0.0, round(expected, 4)}
        assert round(expected, 4) in shifts, "后半拍应该被推后"

    def test_swing_keeps_bar_length(self, make_project):
        project = make_project(swing=0.6, sections={"verse": 4})
        path, _ = compose(str(project), "v1", report=False)[0]
        bar = 4 * 60 / 100
        assert abs(_load(path).get_end_time() / bar - 4) < 0.6


class TestMelodyMotif:
    """旋律要像"一句话"，不是同一句循环：A / A' / B / A''。"""

    def _units(self, path, bars_per_unit=2, bars_total=8):
        bar = 4 * 60 / 100
        units = {}
        for note in _notes(path, "lead"):
            index = min(bars_total // bars_per_unit - 1,
                        int(note.start / (bars_per_unit * bar)))
            units.setdefault(index, []).append(
                (note.pitch, round(note.end - note.start, 2))
            )
        return [units[k] for k in sorted(units)]

    def test_units_differ(self, make_project):
        """用单一和弦，把"和弦变了"这个变量排除掉。

        整首只有一个和弦时，句子之间还不同 —— 那才是动机变奏起的作用；
        用多和弦进行的话，光换和弦就能让四句不同，测不出来。
        """
        project = make_project(
            style="cinematic", progression=["i"], sections={"chorus": 8}
        )
        path, _ = compose(str(project), "v1", report=False)[0]
        shapes = [tuple(u) for u in self._units(path)]
        assert len(shapes) == 4
        assert len(set(shapes)) >= 3, f"四句里至少要有三句不一样，实际 {shapes}"

    def test_cycle_declares_variation(self):
        from patterns.lead import MOTIF_CYCLE

        kinds = [kind for _, kind in MOTIF_CYCLE]
        assert len(set(kinds)) >= 3, f"句法里要有真变奏，实际 {kinds}"
        assert "cadence" in kinds, "四句里应该有一句收束"

    def test_no_unit_is_a_single_note(self, make_project):
        """每句内部得有起伏，否则就是"一个音按了四下"。"""
        project = make_project(style="cinematic", sections={"chorus": 8})
        path, _ = compose(str(project), "v1", report=False)[0]
        for index, unit in enumerate(self._units(path), 1):
            assert len({pitch for pitch, _ in unit}) >= 2, f"第 {index} 句只有一个音高：{unit}"

    def test_lead_stays_in_style_range(self, make_project):
        from core.styles import resolve

        project = make_project(style="cinematic", sections={"chorus": 16})
        path, _ = compose(str(project), "v1", report=False)[0]
        low, high = resolve("cinematic")["lead"]["range"]
        pitches = [n.pitch for n in _notes(path, "lead")]
        assert min(pitches) >= low and max(pitches) <= high, \
            f"旋律跑出风格音区 {low}~{high}：{min(pitches)}~{max(pitches)}"

    def test_variant_rules(self):
        from patterns.lead import _variant

        phrase = [(0, 0.0, 1.0), (1, 2.0, 1.0)]
        up = _variant(phrase, "tail_up", 4)
        assert up[1][0] == 2 and up[0] == phrase[0], "上扬只该改最后一个音的音级"
        down = _variant(phrase, "tail_down", 4)
        assert down[1][0] == 0
        cadence = _variant(phrase, "cadence", 4)
        assert cadence[1][2] > phrase[1][2], "收束要拉长尾音"
        assert cadence[1][0] == phrase[1][0], "收束不该改音高（会躺平）"
        assert _variant(phrase, "plain", 4) == phrase


class TestProjectIndex:
    """projects/ 不进 git，所以靠 INDEX.md 让人（和别的工具）看见有哪些歌。"""

    def test_written_beside_projects(self, make_project):
        project = make_project(sections={"verse": 2})
        compose(str(project), "v1", report=False)

        index = project.parent / "INDEX.md"
        assert index.exists(), "生成后应该在 projects 根目录写出 INDEX.md"
        text = index.read_text(encoding="utf-8")
        assert project.name in text
        assert "v1" in text

    def test_lists_latest_version(self, make_project):
        project = make_project(sections={"verse": 2})
        compose(str(project), "v1", report=False)
        compose(str(project), "v2", report=False)

        text = (project.parent / "INDEX.md").read_text(encoding="utf-8")
        row = next(line for line in text.splitlines() if project.name in line)
        assert "v2" in row, f"索引应该写最新版本，实际：{row}"
        assert "v1" not in row


class TestVersionDiff:
    def test_no_diff_for_first_version(self, make_project, capsys):
        project = make_project(sections={"verse": 2})
        compose(str(project), "v1", report=False)
        assert "[diff]" not in capsys.readouterr().out

    def test_reports_change_between_versions(self, make_project, capsys):
        import json

        project = make_project(sections={"verse": 2})
        compose(str(project), "v1", report=False)
        capsys.readouterr()

        cfg = json.loads((project / "config.json").read_text(encoding="utf-8"))
        cfg["sections"] = {"verse": 4}          # 多两小节 → 音符数必然变
        (project / "config.json").write_text(
            json.dumps(cfg, ensure_ascii=False), encoding="utf-8"
        )
        compose(str(project), "v2", report=False)

        out = capsys.readouterr().out
        assert "[diff] 相比 v1" in out, out
        assert "音" in out


class TestBuildUp:
    """段落内渐强：密度在段内爬升，而不是整段一个密度。"""

    def _drum_counts(self, make_project, **overrides):
        project = make_project(sections={"chorus": 8}, **overrides)
        path, _ = compose(str(project), "v1", report=False)[0]
        bar = 4 * 60 / 100
        counts = [0] * 8
        for note in _notes(path, "drums"):
            counts[min(7, int(note.start / bar))] += 1
        return counts

    def test_up_gets_denser(self, make_project):
        counts = self._drum_counts(
            make_project, arrange={"chorus": {"build": "up", "fill": False, "crash": False}}
        )
        assert counts[0] < counts[-1], f"渐强应该越打越密，实际 {counts}"

    def test_down_gets_sparser(self, make_project):
        counts = self._drum_counts(
            make_project, arrange={"chorus": {"build": "down", "fill": False, "crash": False}}
        )
        assert counts[0] > counts[-1], f"渐弱应该越打越稀，实际 {counts}"

    def test_none_is_flat(self, make_project):
        counts = self._drum_counts(
            make_project, arrange={"chorus": {"build": None, "fill": False, "crash": False}}
        )
        assert len(set(counts)) == 1, f"不写 build 时每小节应该一样密，实际 {counts}"

    def test_density_at_is_monotonic(self):
        """直接测插值函数：段内进度单调 → 密度档单调。"""
        from core.arrange import DRUM_LADDER
        from core.context import Ctx

        ctx = Ctx(bpm=100, start_bar=0, bars=8, progression=["Am"], chords={"Am": (0, 3, 7)},
                  vel_scale=1.0, style="pop", style_spec={}, density="full", build="up")
        levels = [ctx.density_at(i) for i in range(8)]
        indexes = [DRUM_LADDER.index(v) for v in levels]
        assert indexes == sorted(indexes), f"渐强不该回退：{levels}"
        assert levels[0] != levels[-1]
        assert levels[-1] == "full", "最后一小节要打到本段密度"

    def test_single_bar_section_gets_target_density(self):
        """只有一小节的段落没有"渐变"可言，必须直接给本段密度。"""
        from core.context import Ctx

        ctx = Ctx(bpm=100, start_bar=0, bars=1, progression=["Am"], chords={"Am": (0, 3, 7)},
                  vel_scale=1.0, style="pop", style_spec={}, density="full", build="up")
        assert ctx.density_at(0) == "full"


class TestBassLock:
    """bass 与底鼓咬合：kick 响的地方 bass 也要响（长音铺底型除外）。"""

    def test_every_kick_has_a_bass_note(self, make_project):
        """造一个 kick 落在 bass 节奏型之外的情况，咬合必须把它补上。

        pop 默认的 kick 本来就压在 bass 的正拍上，那样测不出咬合有没有生效，
        所以这里用 style_tweaks 往 1.25 拍塞一个 kick（bass 原本不弹那里）。
        """
        from core.theory import GM_DRUM

        project = make_project(
            style="pop",
            sections={"verse": 2, "chorus": 2},
            style_tweaks={"drums": {"full": [
                ("kick", 0.0, 0.1, 96), ("kick", 1.25, 0.1, 80),
                ("snare", 2.0, 0.1, 74), ("hat", 0.5, 0.05, 30),
            ]}},
        )
        path, _ = compose(str(project), "v1", report=False)[0]
        kicks = [round(n.start, 3) for n in _notes(path, "drums")
                 if n.pitch == GM_DRUM["kick"]]
        bass = {round(n.start, 3) for n in _notes(path, "bass")}

        assert kicks, "这个配置应该有底鼓"
        missing = [k for k in kicks if k not in bass]
        assert not missing, f"这些底鼓落点上 bass 没咬住：{missing}"

    def test_long_note_style_not_chopped(self, make_project):
        """cinematic 是长音铺底，lock_kick 关掉，每小节仍只有一个长音。"""
        project = make_project(style="cinematic", sections={"verse": 4})
        path, _ = compose(str(project), "v1", report=False)[0]
        bass = _notes(path, "bass")

        assert len(bass) == 4, f"cinematic 每小节应只有一个长音，实际 {len(bass)} 个"
        assert max(n.end - n.start for n in bass) > 1.5, "长音应该还在，没被切成短音"

    def test_lock_does_not_duplicate_existing_hits(self, make_project):
        """风格节奏型已经在 kick 上写过音的地方，不该再加一个重复音。"""
        project = make_project(style="pop", sections={"verse": 2})
        path, _ = compose(str(project), "v1", report=False)[0]
        starts = [round(n.start, 3) for n in _notes(path, "bass")]
        assert len(starts) == len(set(starts)), "同一拍位不该有两个 bass 音"


class TestCounter:
    def test_counter_only_in_gaps(self, make_project):
        project = make_project(
            sections={"verse": 2, "chorus": 4},
            arrange={"chorus": {"counter": True}},
        )
        path, _ = compose(str(project), "v1", report=False)[0]
        lead = _notes(path, "lead")
        counter = _notes(path, "counter")

        assert counter, "副歌开了 counter，应该有音"
        for n in counter:
            for m in lead:
                assert not (m.start < n.end - 1e-6 and n.start < m.end - 1e-6), \
                    "副旋律不能和主旋律同时响"

    def test_counter_below_lead(self, make_project):
        project = make_project(
            sections={"verse": 2, "chorus": 2},
            arrange={"chorus": {"counter": True}},
        )
        path, _ = compose(str(project), "v1", report=False)[0]
        counter = [n.pitch for n in _notes(path, "counter")]
        lead = [n.pitch for n in _notes(path, "lead")]
        assert counter and max(counter) <= max(lead)

    def test_pad_yields_to_counter(self, make_project):
        # 副旋律也是"线"，pad 同音叠置会把它磨平
        project = make_project(sections={"verse": 2})
        path, _ = compose(str(project), "v1", report=False)[0]
        assert _collisions(_notes(path, "counter"), _notes(path, "pad")) == 0

    def test_high_voice_sits_above_lead(self, make_project):
        """上方对位允许和主旋律同时响，但必须明显在上面（>=3 个半音）。"""
        project = make_project(
            sections={"verse": 2, "chorus": 4},
            arrange={"chorus": {"counter": True, "counter_voice": "high"}},
        )
        path, _ = compose(str(project), "v1", report=False)[0]
        lead = _notes(path, "lead")
        counter = _notes(path, "counter")

        overlapping = [
            (c.pitch, m.pitch)
            for c in counter for m in lead
            if m.start < c.end - 1e-6 and c.start < m.end - 1e-6
        ]
        assert overlapping, "高位副旋律应该和主旋律有重叠，否则它是 low 不是 high"
        for mine, theirs in overlapping:
            assert mine - theirs >= 3, f"counter {mine} 与 lead {theirs} 只差 {mine - theirs} 个半音"

    def test_high_voice_plays_more_than_low(self, make_project):
        """low 只在空档出声；high 可以同时响，所以副歌音符数应该更多。"""
        def count(voice):
            project = make_project(
                sections={"verse": 2, "chorus": 4},
                arrange={"chorus": {"counter": True, "counter_voice": voice}},
            )
            path, _ = compose(str(project), "v1", report=False)[0]
            bar = 4 * 60 / 100
            return len([n for n in _notes(path, "counter") if n.start >= 2 * bar])

        assert count("high") > count("low")


class TestOccupiedScope:
    """`occupied` 是全曲共享的字典，键必须是绝对小节号。

    曾经键用的是段落内的小节号：主歌第 1 小节主旋律占的音高，会让副歌第 1 小节
    的 pad / arp 也白白让开 —— 表现为"pad 莫名少音"，而且换编排就变，很难查。
    """

    def _ctx(self, start_bar, shared):
        from core.context import Ctx

        return Ctx(
            bpm=120, start_bar=start_bar, bars=2, progression=["Am"],
            chords={"Am": (0, 3, 7)}, vel_scale=1.0, style="pop",
            style_spec={}, occupied=shared,
        )

    def test_same_local_bar_different_section(self):
        shared = {}
        verse = self._ctx(4, shared)
        chorus = self._ctx(12, shared)

        verse.occupy(0, [60])
        assert verse.is_occupied(0, 60)
        assert not chorus.is_occupied(0, 60), "主歌第 1 小节占的音高不该漏到副歌第 1 小节"

    def test_same_section_still_works(self):
        ctx = self._ctx(4, {})
        ctx.occupy(1, [64])
        assert ctx.is_occupied(1, 64)
        assert not ctx.is_occupied(0, 64)


class TestCueSheet:
    def test_written_next_to_midi(self, make_project):
        project = make_project(sections={"intro": 2, "verse": 2, "chorus": 4, "outro": 2})
        path, _ = compose(str(project), "v1", report=False)[0]

        cue = path.replace(".mid", ".cues.md")
        assert (project / "music" / "output" / f"{project.name}-v1.cues.md").exists()

        text = open(cue, encoding="utf-8").read()
        assert "riser" in text and "impact" in text
        assert "小节.拍" in text

    def test_manual_cue_included(self, make_project):
        project = make_project(cues=[{"bar": 3, "beat": 2, "what": "whoosh"}])
        path, _ = compose(str(project), "v1", report=False)[0]
        text = open(path.replace(".mid", ".cues.md"), encoding="utf-8").read()
        assert "whoosh" in text and "3.2" in text
