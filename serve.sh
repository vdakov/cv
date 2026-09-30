#!/usr/bin/env bash
#
# Run local CV preview server at http://localhost:8000
# Usage:
#   ./serve.sh [port]
#

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PYTHON_BIN="$(which python3 || echo "python")"

exec "$PYTHON_BIN" "$DIR/serve.py" "$@"
