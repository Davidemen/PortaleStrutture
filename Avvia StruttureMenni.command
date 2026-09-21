#!/bin/sh
# Avvia StruttureMenni: server locale + browser. Richiede "uv" (https://docs.astral.sh/uv/).
cd "$(dirname "$0")" || exit 1
if ! command -v uv >/dev/null 2>&1; then
  echo "uv non trovato. Installarlo da https://docs.astral.sh/uv/ e riprovare."
  exit 1
fi
exec uv run python scripts/avvia.py "$@"
