#!/usr/bin/env bash
# Whole-tree domain route regression for all Sift templates under rules/.
# Wrapper around matrix_route.py: optional geo bootstrap + default --update-cache.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$ROOT"

TOOLS="$ROOT/.cache/tools"
GEO_BIN="${GEO_BIN:-geo}"

if ! command -v geo >/dev/null 2>&1; then
  if [[ -x "$TOOLS/geo" ]]; then
    export PATH="$TOOLS:$PATH"
    GEO_BIN="$TOOLS/geo"
  else
    mkdir -p "$TOOLS"
    arch="$(uname -m)"
    case "$arch" in
      x86_64|amd64) asset=geo-linux-amd64 ;;
      aarch64|arm64) asset=geo-linux-arm64 ;;
      *) asset=geo-linux-amd64 ;;
    esac
    echo "== bootstrap MetaCubeX geo ($asset) into $TOOLS =="
    if curl -fsSL "https://github.com/MetaCubeX/geo/releases/download/v1.1/${asset}" -o "$TOOLS/geo"; then
      chmod +x "$TOOLS/geo"
      export PATH="$TOOLS:$PATH"
      GEO_BIN="$TOOLS/geo"
    else
      echo "[WARN] could not download geo; MetaCubeX rows may fail until geo is on PATH" >&2
    fi
  fi
fi

# Default: refresh caches then run full matrix with assertions.
# Pass-through extra args, e.g. --no-assert, --domain foo.com, --templates DW-f AC-f
exec python3 "$ROOT/.agents/skills/sift-route-debug/scripts/matrix_route.py" \
  --geo-bin "$GEO_BIN" \
  --update-cache \
  "$@"
