#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

fail() {
    local status=$?
    echo >&2
    echo "Game belum dapat dijalankan. Periksa pesan di atas dan README.md." >&2
    if [[ -t 0 ]]; then
        read -r -p "Tekan Enter untuk menutup... " _ || true
    fi
    exit "${status:-1}"
}
trap fail ERR

EXE="dist/SetelahJamMalam.exe"
if [[ -f "$EXE" ]]; then
    if command -v wine >/dev/null 2>&1; then
        wine "$EXE"
        exit 0
    elif [[ "$(uname -s)" =~ ^(MINGW|MSYS|CYGWIN) ]]; then
        "$EXE"
        exit 0
    else
        echo "Executable Windows ditemukan, tetapi Wine tidak tersedia; mencoba menjalankan source." >&2
    fi
fi

if [[ ! -x ".venv/bin/python" ]]; then
    python3 -m venv .venv
fi

PYTHON=".venv/bin/python"
if ! "$PYTHON" -c 'import pygame' >/dev/null 2>&1; then
    "$PYTHON" -m pip install -r requirements.txt
fi
"$PYTHON" main.py

trap - ERR
