#!/usr/bin/env bash
# 看 8 个功能槽可选的乐器、编制预设、某个项目当前用什么
# 用法见 python tools/instruments.py --help
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
source venv/bin/activate

python tools/instruments.py "$@"
