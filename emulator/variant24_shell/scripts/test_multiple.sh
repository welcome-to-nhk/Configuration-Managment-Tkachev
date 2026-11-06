#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
python3 src/shell_emulator.py --vfs configs/vfs_multiple --script scripts/demo_stage3.txt
