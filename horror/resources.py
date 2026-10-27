"""Resolve bundled assets identically in source and PyInstaller builds."""
from pathlib import Path

ASSET_ROOT = Path(__file__).resolve().parents[1] / "assets"


def asset_path(*parts):
    return ASSET_ROOT.joinpath(*parts)
