"""Curate original CC0 foley. Game runtime never downloads audio."""
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "impact": "https://kenney.nl/assets/impact-sounds",
    "rpg": "https://kenney.nl/assets/rpg-audio",
}


def main():
    out = ROOT / "assets/audio"
    out.mkdir(parents=True, exist_ok=True)
    files = {"impact": [f"footstep_{material}_{i:03}.ogg" for material in ("concrete", "wood", "grass") for i in range(5)]}
    files["impact"] += ["impactGlass_medium_000.ogg", "impactGlass_light_000.ogg", "impactPunch_medium_000.ogg"]
    files["rpg"] = ["doorOpen_1.ogg", "doorOpen_2.ogg", "doorClose_1.ogg", "doorClose_2.ogg",
                    "cloth1.ogg", "cloth3.ogg", "metalClick.ogg"]
    records = []
    for pack, names in files.items():
        with zipfile.ZipFile(ROOT / "build/audio-source" / (pack + ".zip")) as archive:
            for name in names:
                data = archive.read("Audio/" + name)
                (out / name).write_bytes(data)
                records.append({"file": name, "source": SOURCES[pack], "sha256": hashlib.sha256(data).hexdigest()})
            license_name = next(n for n in archive.namelist() if n.lower().endswith("license.txt"))
            (out / (pack + "-License.txt")).write_bytes(archive.read(license_name))
    (out / "manifest.json").write_text(json.dumps({"creator": "Kenney", "license": "CC0-1.0", "files": records}, indent=2), encoding="utf-8")
    print("Imported", len(records), "original foley recordings")


if __name__ == "__main__":
    main()
