#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)"
INPUT="${1:-$ROOT/packs/caret/fixtures/demo_geometry.json}"
OUT="${2:-$ROOT/packs/caret/caret_quantum_result.json}"
PYTHONPATH="$ROOT/game-agent-infra" python3 "$ROOT/tools/caret_quantum_speedrun.py" "$INPUT" -o "$OUT"
printf 'CARET quantum speedrun complete: %s\n' "$OUT"
printf 'SHA256: '
sha256sum "$OUT" | cut -d' ' -f1
