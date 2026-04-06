#!/usr/bin/env bash
# Borough-by-borough bulk download (resumable). Example:
#   ./scripts/download-borough.sh MANHATTAN -v
# Extra args are forwarded to download.py (e.g. --refresh, --start-date).
set -euo pipefail
cd "$(dirname "$0")/.."
exec uv run python download.py --boroughs "$1" "${@:2}"
