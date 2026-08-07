#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests
PYTHONDONTWRITEBYTECODE=1 python3 -B verify.py run --adapter protected --output results/protected-exercise.json
PYTHONDONTWRITEBYTECODE=1 python3 -B verify.py selftest
PYTHONDONTWRITEBYTECODE=1 python3 -B tools/validate_all.py
PYTHONDONTWRITEBYTECODE=1 python3 -B tools/make_index.py --check
