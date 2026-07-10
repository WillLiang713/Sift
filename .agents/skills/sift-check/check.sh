#!/usr/bin/env bash
# Compatibility entry point: keep the validation implementation canonical.
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

exec bash "$ROOT/.claude/skills/sift-check/check.sh" "$@"
