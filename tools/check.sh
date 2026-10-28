#!/usr/bin/env bash
# 产物体检：空轨 / 段落空白 / 小节数不符 / PPQ 不对 / 鼓轨通道错。
# 用法:
#   bash tools/check.sh projects/demo/music/output/demo-v3.mid
#   bash tools/check.sh projects/demo/music/output/demo-v3.mid projects/demo
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
source venv/bin/activate

if [ $# -lt 1 ]; then
  echo "用法: bash tools/check.sh <mid文件> [项目目录]"
  echo "例:   bash tools/check.sh projects/demo/music/output/demo-v3.mid projects/demo"
  exit 2
fi

MID="$1"
# 未指定项目目录时，按 projects/<dir>/music/output/<file>.mid 反推
PROJECT="${2:-$(dirname "$(dirname "$(dirname "$MID")")")}"

if [ -f "$PROJECT/config.json" ]; then
  PYTHONPATH=music python music/core/report.py "$MID" --project "$PROJECT"
else
  echo "[warn] $PROJECT 下没有 config.json，只做基础检查"
  PYTHONPATH=music python music/core/report.py "$MID"
fi
