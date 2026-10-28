#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> 创建 venv"
python3 -m venv venv
source venv/bin/activate

echo "==> 升级 pip"
pip install --upgrade pip

echo "==> 安装依赖"
pip install pretty_midi mido numpy

echo "==> 写 requirements.txt"
pip freeze | grep -E "pretty_midi|mido|numpy" > requirements.txt

echo "==> 环境就绪"
python - <<'PY'
import pretty_midi
print("pretty_midi OK:", pretty_midi.__version__ if hasattr(pretty_midi,'__version__') else 'installed')
PY