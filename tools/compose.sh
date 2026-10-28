#!/usr/bin/env bash
# 生成 MIDI。
# 用法:
#   bash tools/compose.sh <project_dir>              # 版本号自动递增，不覆盖旧版
#   bash tools/compose.sh <project_dir> v3           # 指定版本号
#   bash tools/compose.sh <project_dir> --version v3 # 指定版本号（同上）
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
source venv/bin/activate

PROJECT_DIR="${1:-projects/demo}"

# 解析版本号：支持 "v3" / "--version v3" / 缺省自动递增
if [ "${2:-}" = "--version" ]; then
  VERSION="${3:-auto}"
elif [ -n "${2:-}" ]; then
  VERSION="$2"
else
  VERSION="auto"
fi

OUT_DIR="$PROJECT_DIR/music/output"

if [ "$VERSION" = "auto" ]; then
  mkdir -p "$OUT_DIR"
  LAST="$(ls "$OUT_DIR"/*-v*.mid 2>/dev/null \
          | sed -nE 's/.*-v([0-9]+)\.mid$/\1/p' \
          | sort -n | tail -1)"
  VERSION="v$(( ${LAST:-0} + 1 ))"
fi

# 关键：直接以文件路径运行，不用 python -m（compose.py 内置 sys.path 处理）
python music/core/compose.py --project "$PROJECT_DIR" --version "$VERSION"
