#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
source venv/bin/activate

PROJECT_DIR="${1:-projects/demo}"

# 关键：直接以文件路径运行，不用 python -m
python music/core/compose.py --project "$PROJECT_DIR"
