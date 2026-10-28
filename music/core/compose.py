import os
import sys
import argparse
import pretty_midi

# ===== 路径修复：把 music/ 加入 sys.path =====
_MUSIC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _MUSIC_DIR not in sys.path:
    sys.path.insert(0, _MUSIC_DIR)

from core.config import DEFAULT_CONFIG
from patterns.chords import build as build_chords
from patterns.bass import build as build_bass
from patterns.drums import build as build_drums
from patterns.lead import build as build_lead


def compose(project_dir: str, version: str = "v1"):
    cfg = DEFAULT_CONFIG
    bpm = cfg["bpm"]
    pm = pretty_midi.PrettyMIDI(initial_tempo=bpm)

    insts = {
        "chords": pretty_midi.Instrument(program=0, name="chords"),
        "bass":   pretty_midi.Instrument(program=33, name="bass"),
        "lead":   pretty_midi.Instrument(program=80, name="lead"),
        "drums":  pretty_midi.Instrument(program=0, name="drums", is_drum=True),
        "pad":    pretty_midi.Instrument(program=90, name="pad"),
    }
    for it in insts.values():
        pm.instruments.append(it)

    bar = 0
    for section, bars in cfg["sections"].items():
        if section in ("intro", "verse", "chorus"):
            build_chords(insts["chords"], bpm, bar, bars)
            build_bass(insts["bass"], bpm, bar, bars)
            build_drums(insts["drums"], bpm, bar, bars)
            if section == "chorus":
                build_lead(insts["lead"], bpm, bar, bars)
        bar += bars

    out_dir = os.path.join(project_dir, "music", "output")
    os.makedirs(out_dir, exist_ok=True)
    project_name = os.path.basename(os.path.normpath(project_dir))
    out_file = os.path.join(out_dir, f"{project_name}-{version}.mid")
    pm.write(out_file)
    print("生成完成:", out_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default="projects/demo")
    parser.add_argument("--version", default="v1")
    args = parser.parse_args()
    compose(args.project, args.version)