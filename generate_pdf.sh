#!/usr/bin/env bash
#
# Convenient wrapper script to generate PDF from Markdown CV.
# Usage:
#   ./generate_pdf.sh [output_filename.pdf]
#

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PYTHON_BIN="$(which python3 || echo "python")"

exec "$PYTHON_BIN" "$DIR/generate_pdf.py" "$@"
