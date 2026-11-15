#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

pause_on_error() {
    local status=$?
    if (( status != 0 )); then
        echo "Build gagal. Periksa pesan di atas." >&2
        if [[ -t 0 ]]; then
            read -r -p "Tekan Enter untuk menutup... " _ || true
        fi
    fi
    exit "$status"
}
trap pause_on_error EXIT

case "$(uname -s)" in
    MINGW*|MSYS*|CYGWIN*)
        PYTHON=".venv/Scripts/python.exe"
        if [[ ! -x "$PYTHON" ]]; then
            python -m venv .venv
        fi
        "$PYTHON" -m pip install -r requirements-dev.txt
        "$PYTHON" tools/build_release.py
        echo
        echo "Selesai: dist/SetelahJamMalam.exe dan ZIP portable."
        ;;
    *)
        echo "Build rilis Windows hanya didukung pada Windows (PowerShell/CMD atau Git Bash)." >&2
        echo "Gunakan ./Jalankan.sh untuk menjalankan game dari source di Linux/macOS." >&2
        exit 1
        ;;
esac

trap - EXIT
