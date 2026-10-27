"""Import a curated set of Kenney's CC0 assets from the official ZIP.

Only these PNGs and the original license ship with the game. No paid assets,
API keys, or downloads are needed at game runtime.
"""
import hashlib
import json
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from horror.asset_catalog import TILE_IDS as TILES
URL = "https://kenney.nl/media/pages/assets/top-down-shooter/230204340a-1677694684/kenney_top-down-shooter.zip"


def main():
    archive = ROOT / "build/asset-source/kenney_top-down-shooter.zip"
    archive.parent.mkdir(parents=True, exist_ok=True)
    if not archive.exists():
        urllib.request.urlretrieve(URL, archive)
    destination = ROOT / "assets/kenney"
    destination.mkdir(parents=True, exist_ok=True)
    records = []
    with zipfile.ZipFile(archive) as pack:
        paths = {f"tile_{n:02}.png": f"PNG/Tiles/tile_{n:02}.png" for n in TILES}
        paths["License.txt"] = "License.txt"
        for name, source in paths.items():
            data = pack.read(source)
            (destination / name).write_bytes(data)
            records.append({"file": name, "original": source, "sha256": hashlib.sha256(data).hexdigest()})
    manifest = {"creator": "Kenney Vleugels", "pack": "Top-down Shooter (2016)", "license": "CC0-1.0",
                "page": "https://kenney.nl/assets/top-down-shooter", "source": URL,
                "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(), "files": records}
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Imported {len(records)} files from the original Kenney archive.")


if __name__ == "__main__":
    main()
