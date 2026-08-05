#!/usr/bin/env bash
# Whole-tree domain route regression for all Sift templates under rules/.
# Wrapper around matrix_route.py with default --update-cache.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$ROOT"

# Default: refresh caches then run full matrix with assertions.
# Pass-through extra args, e.g. --no-assert, --domain foo.com, --templates HY-f HY-c
exec python3 "$ROOT/.agents/skills/sift-route-debug/scripts/matrix_route.py" \
  --update-cache \
  "$@"
