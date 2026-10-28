#!/usr/bin/env bash
# 从一句话建新项目（目录 + brief.md + config.json + decisions.md）
# 用法见 python tools/new_song.py --help
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
source venv/bin/activate

python tools/new_song.py "$@"
