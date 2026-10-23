#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if command -v python3 >/dev/null 2>&1; then
  python3 app5_plynne_sledzenie_i_goryl.py
elif command -v python >/dev/null 2>&1; then
  python app5_plynne_sledzenie_i_goryl.py
else
  echo "Python is not installed. Install Python 3 first."
  exit 1
fi
