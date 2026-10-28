#!/usr/bin/env bash
# 生成 MIDI。
# 用法:
#   bash tools/compose.sh <project_dir>              # 版本号自动递增，不覆盖旧版
#   bash tools/compose.sh <project_dir> v3           # 指定版本号
#   bash tools/compose.sh <project_dir> --version v3 # 指定版本号（同上）
#   bash tools/compose.sh <project_dir> --no-report  # 跳过产物体检
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
source venv/bin/activate

PROJECT_DIR="${1:-projects/demo}"
if [ "$#" -gt 0 ]; then shift; fi

# 解析版本号：支持 "v3" / "--version v3" / 缺省自动递增；其余参数原样透传给 compose.py
VERSION="auto"
EXTRA=()
if [ "$#" -gt 0 ]; then
  if [ "$1" = "--version" ]; then
    VERSION="${2:-auto}"
    shift 2 2>/dev/null || shift
  elif [ "${1#-}" = "$1" ]; then
    VERSION="$1"
    shift
  fi
fi
if [ "$#" -gt 0 ]; then
  EXTRA=("$@")
fi

OUT_DIR="$PROJECT_DIR/music/output"

if [ "$VERSION" = "auto" ]; then
  mkdir -p "$OUT_DIR"
  # 用 find 而不是 ls：ls 匹配不到文件会返回非 0，配合 set -o pipefail 会让
  # 全新项目（output 里还没有 .mid）在第一次生成时静默失败。
  LAST="$(find "$OUT_DIR" -maxdepth 1 -name '*-v*.mid' \
          | sed -nE 's/.*-v([0-9]+)\.mid$/\1/p' \
          | sort -n | tail -1)"
  VERSION="v$(( ${LAST:-0} + 1 ))"
fi

# 关键：直接以文件路径运行，不用 python -m（compose.py 内置 sys.path 处理）
if [ "${#EXTRA[@]}" -gt 0 ]; then
  python music/core/compose.py --project "$PROJECT_DIR" --version "$VERSION" "${EXTRA[@]}"
else
  python music/core/compose.py --project "$PROJECT_DIR" --version "$VERSION"
fi
